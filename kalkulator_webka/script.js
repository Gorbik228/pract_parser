(function(){
  const exprEl = document.getElementById('expr');
  const outEl = document.getElementById('out');

  let displayExpr = ''; 
  let inputBuffer = '0'; 
  let waitingForNew = false; 

  function updateDisplay(){
    exprEl.textContent = displayExpr;
    outEl.textContent = inputBuffer;
  }

  function isOp(ch){ return ['+','-','*','/'].includes(ch); }

  function inputNumber(d){
    if(waitingForNew){
      inputBuffer = (d === '.') ? '0.' : d;
      waitingForNew = false;
    } else {
      if(d === '.' && inputBuffer.includes('.')) return;
      inputBuffer = (inputBuffer === '0' && d !== '.') ? d : inputBuffer + d;
    }
    updateDisplay();
  }

  function inputOperator(op){
    flushNumberToExpr();
    if(displayExpr === '' && op === '-'){
      displayExpr = '0-';
    } else {
      if(displayExpr && isOp(displayExpr.slice(-1))){
        displayExpr = displayExpr.slice(0, -1) + op;
      } else {
        displayExpr += op;
      }
    }
    waitingForNew = true;
    updateDisplay();
  }

  function flushNumberToExpr(){
    if(waitingForNew && displayExpr.endsWith('²')) {
    }
    if(inputBuffer !== '' && inputBuffer !== '0'){
      displayExpr += inputBuffer;
      inputBuffer = '0';
    } else if(inputBuffer !== '0'){
      displayExpr += inputBuffer;
      inputBuffer = '0';
    } else if(displayExpr === '' && inputBuffer === '0') {
    } else if(displayExpr && isDigit(displayExpr.slice(-1))) {
    }
  }

  function isDigit(ch){ return /\d/.test(ch); }

  function addLParen(){
    if(inputBuffer !== '0' && !waitingForNew){
      flushNumberToExpr();
      displayExpr += '*(';
    } else {
      displayExpr += '(';
    }
    waitingForNew = true;
    updateDisplay();
  }

  function addRParen(){
    if(!waitingForNew && inputBuffer !== '0'){
      flushNumberToExpr();
    }
    displayExpr += ')';
    waitingForNew = true;
    updateDisplay();
  }

  function sqrtCompute(){
    if(!waitingForNew && inputBuffer !== '0'){
      const val = parseFloat(inputBuffer);
      if(isNaN(val) || val < 0){ inputBuffer = 'Error'; }
      else {
        const res = Math.sqrt(val);
        inputBuffer = Number.isInteger(res) ? String(res) : String(parseFloat(res.toPrecision(12)));
      }
    } else {
      if(displayExpr){
        displayExpr = displayExpr.replace(/(\d+(\.\d+)?|\([^()]*\))$/ , m => `sqrt(${m})`);
      }
    }
    waitingForNew = true;
    updateDisplay();
  }

  function sqrCompute(){
    if(!waitingForNew && inputBuffer !== '0'){
      const val = parseFloat(inputBuffer);
      if(isNaN(val)){ inputBuffer = 'Error'; }
      else {
        const res = val * val;
        inputBuffer = Number.isInteger(res) ? String(res) : String(parseFloat(res.toPrecision(12)));
      }
    } else {
      if(displayExpr){
        if(!displayExpr.endsWith('²')){
          displayExpr += '²';
        }
      }
    }
    waitingForNew = true;
    updateDisplay();
  }

  function clearAll(){
    displayExpr = '';
    inputBuffer = '0';
    waitingForNew = false;
    updateDisplay();
  }

  function toggleSign(){
    if(inputBuffer === 'Error') return;
    inputBuffer = String(parseFloat(inputBuffer) * -1);
    updateDisplay();
  }

  // Процент
  function percent(){
    if(inputBuffer === 'Error') return;
    inputBuffer = String(parseFloat(inputBuffer) / 100);
    updateDisplay();
  }

  function buildEvalExpression(){
    let expr = displayExpr;
    if(!waitingForNew && inputBuffer !== '0') {
      expr += inputBuffer;
    }
    expr = expr.replace(/sqrt\(/g, 'Math.sqrt(');
    expr = expr.replace(/(\d+(\.\d+)?|\([^()]*\))²/g, '($1)**2');
    return expr;
  }

  function safeEval(expr){
    try {
      if(!/^[0-9+\-*/().\sA-Za-z_*^%]+$/.test(expr)) throw new Error('Invalid characters');
      expr = expr.replace(/\^/g, '**');
      if(/[+\-*/]{2,}/.test(expr.replace(/\*\*/g, ''))) throw new Error('Bad operators');
      const result = eval(expr);
      if(typeof result === 'number' && isFinite(result)) return result;
      throw new Error('Evaluation error');
    } catch(e){
      return 'Error';
    }
  }

  function compute(){
    const expr = buildEvalExpression();
    const res = safeEval(expr);
    if(res === 'Error'){
      inputBuffer = 'Error';
    } else {
      inputBuffer = Number.isInteger(res) ? String(res) : String(parseFloat(res.toPrecision(12)));
    }
    displayExpr = '';
    waitingForNew = true;
    updateDisplay();
  }

  function backspace(){
    if(inputBuffer === 'Error'){ clearAll(); return; }
    if(!waitingForNew && inputBuffer !== '0'){
      inputBuffer = inputBuffer.length > 1 ? inputBuffer.slice(0, -1) : '0';
    } else if(displayExpr){
      displayExpr = displayExpr.slice(0, -1);
    }
    updateDisplay();
  }

  document.querySelectorAll('[data-num]').forEach(btn=>{
    btn.addEventListener('click', ()=> inputNumber(btn.getAttribute('data-num')));
  });
  document.querySelectorAll('[data-op]').forEach(btn=>{
    btn.addEventListener('click', ()=> inputOperator(btn.getAttribute('data-op')));
  });

  document.getElementById('equals').addEventListener('click', compute);
  document.getElementById('clear').addEventListener('click', clearAll);
  document.getElementById('neg').addEventListener('click', toggleSign);
  document.getElementById('percent').addEventListener('click', percent);
  document.getElementById('lparen').addEventListener('click', addLParen);
  document.getElementById('rparen').addEventListener('click', addRParen);
  document.getElementById('sqrt').addEventListener('click', sqrtCompute);
  document.getElementById('sqr').addEventListener('click', sqrCompute);

  window.addEventListener('keydown', (e)=>{
    if(e.key >= '0' && e.key <= '9') { inputNumber(e.key); return; }
    if(e.key === '.') { inputNumber('.'); return; }
    if(e.key === 'Enter' || e.key === '=') { e.preventDefault(); compute(); return; }
    if(e.key === 'Backspace'){ backspace(); return; }
    if(e.key === 'Escape'){ clearAll(); return; }
    if(e.key === '+' || e.key === '-' || e.key === '*' || e.key === '/'){ inputOperator(e.key); return; }
    if(e.key === '%'){ percent(); return; }
    if(e.key === '('){ addLParen(); return; }
    if(e.key === ')'){ addRParen(); return; }
    if(e.key.toLowerCase() === 'r'){ sqrtCompute(); return; } 
    if(e.key.toLowerCase() === 's'){ sqrCompute(); return; }  
    if(e.key === '^'){ 
      inputOperator('^'); return;
    }
  });

  updateDisplay();
})();
