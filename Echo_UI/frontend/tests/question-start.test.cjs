const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const test = require('node:test')
const ts = require('typescript')

// Render the real Workspace with controlled hooks and a delayed startRun response.
// No browser, backend, credentials, model calls or additional test dependencies.
const filename = path.join(__dirname, '../src/manager/ManagerApp.tsx')
const source = ts.createSourceFile(filename, fs.readFileSync(filename, 'utf8'), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX)
const included = new Set(['Workspace', 'usePref', 'liveConnection', 'keyOf', 'SUGGESTED_SHORT', 'SUGGESTED', 'GUARDRAIL_EXAMPLE', 'PERIODS'])
const declarations = source.statements.filter((s) =>
  s.name && included.has(s.name.text) || ts.isVariableStatement(s) && s.declarationList.declarations.some((d) => included.has(d.name.text)))
const javascript = ts.transpileModule(declarations.map((s) => s.getText(source)).join('\n'), {
  compilerOptions: { jsx: ts.JsxEmit.React, jsxFactory: 'h', jsxFragmentFactory: 'Fragment', target: ts.ScriptTarget.ES2022 },
}).outputText

function harness(conversations = []) {
  const slots = []
  let cursor = 0
  let resolve, reject
  const response = new Promise((yes, no) => { resolve = yes; reject = no })
  const calls = []
  const context = {
    h: (type, props, ...children) => ({ type, props: { ...props, children } }), Fragment: 'Fragment',
    localStorage: { getItem: () => null, setItem: () => {} },
    document: { getElementById: () => null },
  }
  for (const statement of source.statements) {
    if (ts.isImportDeclaration(statement)) {
      const clause = statement.importClause
      if (clause?.name) context[clause.name.text] = clause.name.text
      for (const item of clause?.namedBindings?.elements ?? []) context[item.name.text] = item.name.text
    } else if (ts.isFunctionDeclaration(statement) && statement.name) context[statement.name.text] = statement.name.text
  }
  context.useState = (initial) => {
    const index = cursor++
    if (!(index in slots)) slots[index] = typeof initial === 'function' ? initial() : initial
    return [slots[index], (next) => { slots[index] = typeof next === 'function' ? next(slots[index]) : next }]
  }
  context.useRef = (initial) => {
    const index = cursor++
    if (!(index in slots)) slots[index] = { current: initial }
    return slots[index]
  }
  Object.assign(context, {
    useEffect: () => {}, useMemo: (fn) => fn(), useCallback: (fn) => fn,
    useAsync: () => ({ data: null, loading: false }),
    useRunEvents: () => ({ events: [], done: null }), agentStates: () => ({}), agentActivity: () => ({}),
    loadConversations: () => conversations, loadThanked: () => ({}), loadWatch: () => [],
    clsx: () => '', SERIES_COLORS: ['green'], TAGLINE: 'Echo',
    api: { startRun: (request) => { calls.push(request); return response } },
  })
  const renderWorkspace = vm.runInNewContext(javascript + '\nWorkspace', context)
  const render = () => {
    cursor = 0
    return renderWorkspace({ manager: { Manager_ID: 'M14', Manager_Name: 'Demo Manager', Primary_Team: 'Team', Primary_Department: 'Dept', Pilot_Assigned_Employees: 10 }, onLeave: () => {} })
  }
  function nodes(tree) {
    if (!tree || typeof tree !== 'object') return []
    if (Array.isArray(tree)) return tree.flatMap(nodes)
    return [tree, ...nodes(tree.props?.children)]
  }
  const find = (tree, predicate) => nodes(tree).find(predicate)
  const findAll = (tree, predicate) => nodes(tree).filter(predicate)
  const text = (node) => typeof node === 'string' ? node : Array.isArray(node) ? node.map(text).join('') : node?.props ? text(node.props.children) : ''
  const open = () => {
    const tree = render()
    find(tree, (n) => n.type === 'button' && text(n) === 'Ask EchoQuestions & answers').props.onClick()
    return render()
  }
  const suggestion = (tree) => find(tree, (n) => n.type === 'button' && text(n).includes("How much of my team's cross-team work"))
  return { render, open, suggestion, find, findAll, calls, resolve, reject, text }
}

test('six rapid suggestion clicks send only one request and create only one chat', async () => {
  const ui = harness()
  const click = ui.suggestion(ui.open()).props.onClick
  for (let i = 0; i < 6; i++) click()
  assert.equal(ui.calls.length, 1)
  ui.resolve({ id: 'demo-run', mode: 'offline' })
  await new Promise(setImmediate)
  assert.equal(ui.findAll(ui.render(), (n) => n.props?.['aria-label']?.startsWith('Delete chat:')).length, 1)
})

test('the selected question and loading state appear before startRun responds', () => {
  const ui = harness()
  ui.suggestion(ui.open()).props.onClick()
  const tree = ui.render()
  const banner = ui.find(tree, (n) => n.type === 'AnswerBand')
  assert.ok(banner, 'the answer banner must appear without waiting for the server')
  assert.equal(banner.props.question, ui.calls[0].question)
  assert.equal(banner.props.busy, true)
  assert.equal(banner.props.preparing, true)
  assert.equal(ui.find(tree, (n) => n.props?.['aria-label'] === 'Preparing answer').props.disabled, true)
  assert.equal(ui.find(tree, (n) => n.type === 'input' && n.props.id === 'ask').props.disabled, true)
  assert.ok(ui.find(tree, (n) => n.props?.role === 'status'), 'announce that the answer is being prepared')
})

test('a successful delayed start creates one chat and keeps further submissions blocked', async () => {
  const ui = harness()
  const click = ui.suggestion(ui.open()).props.onClick
  click()
  ui.resolve({ id: 'demo-run', mode: 'offline' })
  await new Promise(setImmediate)
  const tree = ui.render()
  assert.equal(ui.find(tree, (n) => n.type === 'AnswerBand').props.question, ui.calls[0].question)
  assert.equal(ui.find(tree, (n) => n.type === 'AnswerBand').props.busy, true)
  assert.ok(ui.find(tree, (n) => n.props?.['aria-label'] === `Delete chat: ${ui.calls[0].question}`))
  const form = ui.find(tree, (n) => n.type === 'form')
  form.props.onSubmit({ preventDefault() {} })
  assert.equal(ui.calls.length, 1)
})

test('a failed start displays the error and allows retry without saving a phantom chat', async () => {
  const ui = harness()
  ui.suggestion(ui.open()).props.onClick()
  ui.reject(new Error('Demo preparation failed'))
  await new Promise(setImmediate)
  const tree = ui.render()
  assert.match(ui.text(tree), /Demo preparation failed/)
  assert.equal(ui.find(tree, (n) => n.type === 'input' && n.props.id === 'ask').props.disabled, false)
  assert.equal(ui.find(tree, (n) => n.props?.['aria-label']?.startsWith('Delete chat:')), undefined)
  ui.suggestion(tree).props.onClick()
  await new Promise(setImmediate)
  assert.equal(ui.calls.length, 2)
})

test('rapid Home suggestions share the same submission guard', () => {
  const ui = harness()
  const home = ui.find(ui.render(), (n) => n.type === 'HomeDashboard')
  for (let i = 0; i < 6; i++) home.props.onAsk('How is recognition trending for my team?')
  assert.equal(ui.calls.length, 1)
  assert.equal(ui.find(ui.render(), (n) => n.type === 'AnswerBand').props.question, ui.calls[0].question)
})

test('a pending follow-up shows the new question instead of the previous answer', async () => {
  const previous = { id: 'previous', title: 'Previous question', createdAt: '2026-11-18', messages: [
    { question: 'Previous question', runId: 'previous', mode: 'demo', askedAt: '2026-11-18' },
  ] }
  const ui = harness([previous])
  ui.find(ui.render(), (n) => n.type === 'button' && ui.text(n) === 'Previous question').props.onClick()
  ui.find(ui.render(), (n) => n.type === 'input' && n.props.id === 'ask').props.onChange({ target: { value: 'How is my team morale?' } })
  ui.find(ui.render(), (n) => n.type === 'form').props.onSubmit({ preventDefault() {} })
  let tree = ui.render()
  assert.equal(ui.find(tree, (n) => n.type === 'AnswerBand').props.question, 'How is my team morale?')
  assert.equal(ui.find(tree, (n) => n.type === 'AnswerBand').props.index, 2)
  assert.equal(ui.find(tree, (n) => n.type === 'Brief'), undefined)
  ui.resolve({ id: 'follow-up', mode: 'offline' })
  await new Promise(setImmediate)
  tree = ui.render()
  assert.equal(ui.find(tree, (n) => n.type === 'AnswerBand').props.total, 2)
  assert.equal(ui.find(tree, (n) => n.type === 'EarlierResult').props.message.runId, 'previous')
})
