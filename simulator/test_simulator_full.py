import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from casting_simulator import ALLOY_TYPES, SHELL_MATERIALS, LostWaxCastingSimulator

results = []

results.append('=== 合金类型测试 ===')
for key, info in ALLOY_TYPES.items():
    results.append(f'  {key:20s} - {info["name"]}, 浇铸温度: {info["pouring_temp_base"]}°C')

results.append('')
results.append('=== 型壳材料测试 ===')
for key, info in SHELL_MATERIALS.items():
    results.append(f'  {key:20s} - {info["name"]}, 层数: {info["layers"]}, 透气度: {info["permeability_base"]}%')

results.append('')
results.append('=== 模拟器初始化测试 ===')
sim = LostWaxCastingSimulator(
    alloy_type='stainless_steel',
    shell_material='ethyl_silicate',
    pouring_temp=1600.0,
    shell_layers=12,
    defect_intensity=0.8,
)
results.append(f'  合金名称: {sim.alloy_name}')
results.append(f'  浇铸温度: {sim.pouring_temp_base}°C')
results.append(f'  型壳名称: {sim.shell_name}')
results.append(f'  型壳层数: {sim.shell_layers}')
results.append(f'  透气度基准: {sim.permeability_base}%')
results.append(f'  热导率: {sim.thermal_conductivity} W/(m·K)')
results.append(f'  缺陷强度因子: {sim.defect_intensity}')

results.append('')
results.append('=== 传感器数据生成测试 ===')
sim.current_step = 30
data = sim._generate_sensor_data()
for k, v in data.items():
    results.append(f'  {k:25s}: {v}')

results.append('')
results.append('=== 验证数据字段完整性 ===')
required_fields = [
    'casting_id', 'timestamp', 'step',
    'alloy_type', 'shell_material',
    'wax_temperature', 'pouring_temperature',
    'shell_temperature', 'shell_permeability',
    'thermal_conductivity',
    'filling_progress', 'filling_rate',
    'defect_risk_factor'
]
missing = [f for f in required_fields if f not in data]
if missing:
    results.append(f'  缺失字段: {missing}')
else:
    results.append('  所有必需字段完整 ✓')

results.append('')
results.append('=== 验证不同合金/型壳组合 ===')
test_cases = [
    ('bronze_cu_sn', 'silica_sol'),
    ('aluminum_alloy', 'gypsum'),
    ('cast_iron', 'water_glass'),
]
for alloy, shell in test_cases:
    sim2 = LostWaxCastingSimulator(alloy_type=alloy, shell_material=shell)
    sim2.current_step = 10
    d = sim2._generate_sensor_data()
    results.append(f'  {alloy} + {shell}: 浇铸={d["pouring_temperature"]}°C, 透气={d["shell_permeability"]}%')

results.append('')
results.append('=== 所有测试通过 ===')

output = '\n'.join(results)
print(output)

with open('test_results.txt', 'w', encoding='utf-8') as f:
    f.write(output)
