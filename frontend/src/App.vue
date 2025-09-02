<script setup>
import { ref, computed } from 'vue';

// --- 组件数据定义 ---
const available_components = ref([
    { name: 'Methane', formula: 'CH₄', chineseName: '甲烷' },
    { name: 'Nitrogen', formula: 'N₂', chineseName: '氮气' },
    { name: 'CarbonDioxide', formula: 'CO₂', chineseName: '二氧化碳' },
    { name: 'Ethane', formula: 'C₂H₆', chineseName: '乙烷' },
    { name: 'Propane', formula: 'C₃H₈', chineseName: '丙烷' },
    { name: 'Water', formula: 'H₂O', chineseName: '水' },
    { name: 'Hydrogen', formula: 'H₂', chineseName: '氢气' },
    { name: 'HydrogenSulfide', formula: 'H₂S', chineseName: '硫化氢' },
    { name: 'CarbonMonoxide', formula: 'CO', chineseName: '一氧化碳' },
    { name: 'Oxygen', formula: 'O₂', chineseName: '氧气' },
    { name: 'Isobutane', formula: 'i-C₄H₁₀', chineseName: '异丁烷' },
    { name: 'Butane', formula: 'n-C₄H₁₀', chineseName: '正丁烷' },
    { name: 'Isopentane', formula: 'i-C₅H₁₂', chineseName: '异戊烷' },
    { name: 'Pentane', formula: 'n-C₅H₁₂', chineseName: '正戊烷' },
    { name: 'Hexane', formula: 'n-C₆H₁₄', chineseName: '己烷' },
    { name: 'Heptane', formula: 'n-C₇H₁₆', chineseName: '庚烷' },
    { name: 'Octane', formula: 'n-C₈H₁₈', chineseName: '辛烷' },
    { name: 'Nonane', formula: 'n-C₉H₂₀', chineseName: '壬烷' },
    { name: 'Decane', formula: 'n-C₁₀H₂₂', chineseName: '癸烷' },
    { name: 'Helium', formula: 'He', chineseName: '氦气' },
    { name: 'Argon', formula: 'Ar', chineseName: '氩气' },
]);

const defaultValues = [
  { name: 'Methane', fraction: 0.961651 },
  { name: 'Nitrogen', fraction: 0.008606 },
  { name: 'CarbonDioxide', fraction: 0.004567 },
  { name: 'Ethane', fraction: 0.01998 },
  { name: 'Propane', fraction: 0.003859 },
  { name: 'Butane', fraction: 0.000950 },
  { name: 'Pentane', fraction: 0.000138 },
  { name: 'Hexane', fraction: 0.000249 },
];

const component_map = computed(() => {
  return available_components.value.reduce((map, comp) => {
    map[comp.name] = comp;
    return map;
  }, {});
});


// --- 工况参数 ---
const T_work = ref(350.0);
const P_work_kPa = ref(10000.0);
const Q_work = ref(1000.0);

// --- 标况参数 ---
const T_base = ref(293.15);
const P_base_kPa = ref(101.325);

const base_components = ref(JSON.parse(JSON.stringify(defaultValues)));

// --- 结果 ---
const result_work = ref(null);
const result_base = ref(null);
const Q_base = ref(null);
const error = ref(null);
const loading = ref(false);

const total_fraction = computed(() => {
  return base_components.value.reduce((sum, comp) => sum + (Number(comp.fraction) || 0), 0);
});

const is_fraction_valid = computed(() => {
    return Math.abs(total_fraction.value - 1.0) < 1e-6;
});

// --- 方法 ---
function addComponent() {
  base_components.value.push({ name: '', fraction: 0.0 });
}

function removeComponent(index) {
  base_components.value.splice(index, 1);
}

function loadDefaultValues() {
  base_components.value = JSON.parse(JSON.stringify(defaultValues));
}

async function calculate() {
  loading.value = true;
  result_work.value = null;
  result_base.value = null;
  Q_base.value = null;
  error.value = null;

  if (!is_fraction_valid.value) {
    error.value = `摩尔分数总和必须为1，但当前为 ${total_fraction.value.toFixed(6)}。请检查输入值。`;
    loading.value = false;
    return;
  }
  
  // 从基础组分中分离氢气
  let hydro_frac = 0;
  const other_components = [];
  base_components.value.forEach(comp => {
      if (comp.name === 'Hydrogen') {
          hydro_frac += Number(comp.fraction) || 0;
      } else {
          other_components.push(comp);
      }
  });

  const componentsPayload = other_components.reduce((acc, comp) => {
    if (comp.name && comp.fraction > 0) {
      acc[comp.name] = comp.fraction;
    }
    return acc;
  }, {});

  const payload_work = {
    T: T_work.value,
    P_kPa: P_work_kPa.value,
    hydrogen_fraction: hydro_frac,
    base_components: componentsPayload,
  };

  const payload_base = {
    T: T_base.value,
    P_kPa: P_base_kPa.value,
    hydrogen_fraction: hydro_frac,
    base_components: componentsPayload,
  };

  try {
    const [response_work, response_base] = await Promise.all([
      fetch('/compress-factor-calculate/api/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload_work),
      }),
      fetch('/compress-factor-calculate/api/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload_base),
      })
    ]);

    if (!response_work.ok) {
      const errorData = await response_work.json();
      throw new Error(`工况计算错误: ${errorData.detail || `HTTP error! status: ${response_work.status}`}`);
    }
    if (!response_base.ok) {
      const errorData = await response_base.json();
      throw new Error(`标况计算错误: ${errorData.detail || `HTTP error! status: ${response_base.status}`}`);
    }

    const data_work = await response_work.json();
    const data_base = await response_base.json();

    result_work.value = data_work;
    result_base.value = data_base;

    // Calculate standard flow
    const z_work = data_work.compression_factor;
    const z_base = data_base.compression_factor;
    if (z_work && z_base && P_base_kPa.value > 0 && T_work.value > 0) {
        Q_base.value = Q_work.value * (P_work_kPa.value / P_base_kPa.value) * (T_base.value / T_work.value) * (z_base / z_work);
    }

  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="container">
    <h1>AGA8-92DC压缩因子计算器</h1>

    <div class="main-layout">
      <!-- Input Column -->
      <div class="input-column">
        <div class="card">
          <div class="card-header">
            <h2>输入参数</h2>
          </div>
         <fieldset class="conditions-group">
             <legend>工况参数</legend>
             <div class="input-group">
               <label for="temp_work">工况温度 (K)</label>
               <input id="temp_work" type="number" v-model.number="T_work" />
             </div>
             <div class="input-group">
               <label for="pressure_work">工况压力 (kPa)</label>
               <input id="pressure_work" type="number" v-model.number="P_work_kPa" />
             </div>
             <div class="input-group">
               <label for="flow_work">工况流量 (m³/h)</label>
               <input id="flow_work" type="number" v-model.number="Q_work" />
             </div>
          </fieldset>
         <fieldset class="conditions-group">
             <legend>标况参数</legend>
             <div class="input-group">
               <label for="temp_base">标况温度 (K)</label>
               <input id="temp_base" type="number" v-model.number="T_base" />
             </div>
             <div class="input-group">
               <label for="pressure_base">标况压力 (kPa)</label>
               <input id="pressure_base" type="number" v-model.number="P_base_kPa" />
             </div>
         </fieldset>
        </div>

        <div class="card">
          <div class="card-header">
            <h2>气体组分</h2>
            <button @click="loadDefaultValues" class="load-defaults-btn">载入典型组分</button>
          </div>
          <div v-for="(component, index) in base_components" :key="index" class="component-row">
            <select v-model="component.name">
              <option disabled value="">请选择一个组分</option>
              <option v-for="comp in available_components" :key="comp.name" :value="comp.name">
                {{ comp.name }} ({{ comp.formula }}) - {{ comp.chineseName }}
              </option>
            </select>
            <input type="number" v-model.number="component.fraction" placeholder="摩尔分数" step="0.0001" />
            <button @click="removeComponent(index)" class="remove-btn">移除</button>
          </div>
          <button @click="addComponent" class="add-btn">添加组分</button>
        </div>
        <div class="card-footer">
            <p>
              <strong>总摩尔分数:</strong>
              <span :class="{'fraction-error': !is_fraction_valid}">{{ total_fraction.toFixed(6) }}</span>
            </p>
            <p v-if="!is_fraction_valid" class="fraction-error-message">
              总摩尔分数必须接近1。
            </p>
          </div>
         <button @click="calculate" class="calculate-btn" :disabled="loading || !is_fraction_valid">
            {{ loading ? '计算中...' : '计 算' }}
          </button>
      </div>

      <!-- Results Column -->
      <div class="results-column">
        <div class="card sticky-card">
           <div class="card-header">
            <h2>计算结果</h2>
          </div>
          <div v-if="loading" class="loading-spinner">
            <p>正在计算，请稍候...</p>
          </div>
          <div v-if="error" class="error-card">
            <h3>错误</h3>
            <p>{{ error }}</p>
          </div>
         <div v-if="result_work && result_base" class="result-content">
           <div class="result-grid">
               <p class="result-item"><strong>工况 Z 因子:</strong> <span>{{ result_work.compression_factor?.toFixed(6) }}</span></p>
               <p class="result-item"><strong>标况 Z 因子:</strong> <span>{{ result_base.compression_factor?.toFixed(6) }}</span></p>
               <p class="result-item result-item-full"><strong>标况流量 (Nm³/h):</strong> <span>{{ Q_base?.toFixed(4) }}</span></p>
           </div>
           
           <h3>最终组分比例:</h3>
           <ul class="result-list">
             <li v-for="(frac, compName) in result_work.final_components" :key="compName">
                <span>{{ component_map[compName] ? `${component_map[compName].chineseName} (${component_map[compName].formula})` : compName }}</span>
                <span>{{ frac.toFixed(6) }}</span>
             </li>
           </ul>
         </div>
          <div v-if="!result_work && !result_base && !error && !loading" class="placeholder-text">
           <p>点击“计算”后，结果将在此处显示。</p>
         </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 2rem;
    }
    
    h1 {
      text-align: center;
      color: var(--text-color);
      font-weight: 600;
      margin-bottom: 2.5rem;
      font-size: 2.2rem;
    }
    
    .main-layout {
      display: flex;
      gap: 2rem;
      align-items: flex-start;
    }
    
    .input-column {
      flex: 2;
      display: flex;
      flex-direction: column;
      gap: 2rem;
    }
    
    .results-column {
      flex: 1;
    }
    
    .card {
      background: var(--card-bg-color);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 2rem;
      box-shadow: 0 4px 12px var(--shadow-color);
    }
    
    .sticky-card {
      position: sticky;
      top: 2rem;
    }
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid var(--border-color);
    }
    
    h2 {
      margin: 0;
      font-size: 1.5rem;
      font-weight: 600;
    }
    
    .input-group, .component-row {
      display: grid;
      gap: 1rem;
      margin-bottom: 1.25rem;
    }

    .input-group {
      grid-template-columns: 1fr 3fr;
       align-items: center;
    }
    
    .component-row {
      grid-template-columns: 3fr 2fr auto;
      align-items: center;
    }
    
    label {
      font-weight: 500;
      text-align: right;
      padding-right: 1rem;
    }
    
    input, select {
      padding: 0.6rem 1rem;
      border-radius: 8px;
      border: 1px solid var(--border-color);
      font-size: 1rem;
      width: 100%;
      box-sizing: border-box;
    }
    
    button {
      padding: 0.6rem 1.5rem;
      border: 1px solid transparent;
      border-radius: 8px;
      color: #fff;
      cursor: pointer;
      font-size: 0.95rem;
      font-weight: 500;
      transition: all 0.2s ease;
    }
    
    .load-defaults-btn {
      background-color: transparent;
      color: var(--primary-color);
      border-color: var(--primary-color);
    }
    
    .add-btn {
      background-color: var(--primary-color);
      justify-self: start;
    }
    
    .calculate-btn {
      background-color: var(--success-color);
      font-size: 1.2rem;
      padding: 0.8rem;
    }
     .calculate-btn:disabled {
      background-color: #6c757d;
      cursor: not-allowed;
    }
    
    .remove-btn {
      background-color: var(--danger-color);
      padding: 0.6rem 1rem;
    }
    
    .result-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .result-item {
        font-size: 1.1rem;
        font-weight: 500;
        padding: 1rem;
        background-color: #e9f7ef;
        border-radius: 8px;
        text-align: center;
        margin: 0;
    }
    .result-item strong {
        display: block;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
        color: #343a40;
    }
    .result-item span {
        font-size: 1.3rem;
        font-weight: 600;
        color: var(--success-color);
    }
    
    .result-item-full {
        grid-column: 1 / -1;
    }
    .result-item-full span {
      color: var(--primary-color)
    }
    
    .result-list {
        list-style: none;
        padding: 0;
        max-height: 400px;
        overflow-y: auto;
    }

    .result-list li {
        display: flex;
        justify-content: space-between;
        padding: 0.75rem 0.5rem;
        border-bottom: 1px solid #f1f3f5;
    }

    .result-list li:last-child {
        border-bottom: none;
    }

    .error-card {
        background-color: #fff0f0;
        color: #d94a28;
        border: 1px solid #ffc0c0;
        border-radius: 8px;
        padding: 1rem;
    }
    .placeholder-text, .loading-spinner {
        text-align: center;
        color: #6c757d;
        padding: 4rem 1rem;
    }
    .conditions-group {
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
    }
    .conditions-group legend {
      font-weight: 600;
      padding: 0 0.5rem;
      margin-left: 1rem;
      color: var(--text-color);
    }
    .card-footer {
      padding-top: 1rem;
      margin-top: 1rem;
      border-top: 1px solid var(--border-color);
    }
    .fraction-error {
        color: var(--danger-color);
        font-weight: bold;
    }
    .fraction-error-message {
        color: var(--danger-color);
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
</style>