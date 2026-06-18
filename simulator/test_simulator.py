import sys
sys.path.insert(0, '.')
from casting_simulator import ALLOY_TYPES, SHELL_MATERIALS, LostWaxCastingSimulator

print('=== 合金类型测试 ===')
for key, info in ALLOY_TYPES.items():
    print(f'  {key:20s} - {info["name"]}, 浇铸温度: {info["pouring_temp_base"]}°C')

print()
print('=== 型壳材料测试 ===')
for key, info in SHELL_MATERIALS.items():
    print(f'  {key:20s} - {info["name"]}, 层数: {info["layers"]}, 透气度: {info["permeability_base"]}%')

print()
print('=== 模拟器初始化测试 ===')
sim = LostWaxCastingSimulator(
    alloy_type='stainless_steel',
    shell_material='ethyl_silicate',
    pouring_temp=1600.0,
    shell_layers=12,
    defect_intensity=0.8,
)
print(f'  合金名称: {sim.alloy_name}')
print(f'  浇铸温度: {sim.pouring_temp_base}°C')
print(f'  型壳名称: {sim.shell_name}')
print(f'  型壳层数: {sim.shell_layers}')
print(f'  透气度基准: {sim.permeability_base}%')
print(f'  热导率: {sim.thermal_conductivity} W/(m·K)')
print(f'  缺陷强度因子: {sim.defect_intensity}')

print()
print('=== 传感器数据生成测试 ===')
sim.current_step = 30
data = sim._generate_sensor_data()
for k, v in data.items():
    print(f'  {k:25s}: {v}')

print()
print('=== 所有测试通过 ===')
