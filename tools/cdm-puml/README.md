# CDM → PlantUML 可视化与双语标签生成器

该工具集成于 Microsoft/CDM 仓库，支持从 Common Data Model 清单中递归发现实体关系，并输出包含中英双语标签的 PlantUML 类图。

## 功能特性

- ✅ BFS 递归遍历实体之间的关联与继承，支持深度控制与继承覆盖配置。
- ✅ 通过 CSV/Excel 翻译资源生成中英双语标签，按主语言优先、备用语言回退。
- ✅ PlantUML 渲染主题可配置，支持隐藏属性、批量聚合根生成、资源索引导出。
- ✅ 兼容 `cdm.objectmodel` 与 `commondatamodel.objectmodel` 命名空间。

## 安装与准备

1. 建议在仓库根目录创建虚拟环境：
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows PowerShell: .\.venv\Scripts\Activate.ps1
   ```
2. 安装依赖：
   ```bash
   pip install -e tools/cdm-puml
   ```
3. （可选）根据需求修改 `tools/cdm-puml/config/` 下的继承覆盖、聚合根配置或主题文件。
4. 将翻译资源放置在 `tools/cdm-puml/overrides/i18n/`，支持 CSV 或 Excel，列结构见示例。

## 使用示例

### 1. 生成单张类图
```bash
python tools/cdm-puml/generate_puml.py \
  --resources Product Service Customer \
  --depth 2 \
  --language-mode both \
  --output tools/cdm-puml/dist/puml/model_depth_2.puml
```

### 2. 隐藏属性仅展示实体关系
```bash
python tools/cdm-puml/generate_puml.py -r Party Organization \
  --depth 3 --hide-attributes \
  -o tools/cdm-puml/dist/puml/party_relations.puml
```

### 3. 仅对起始实体展开继承
```bash
python tools/cdm-puml/generate_puml.py -r CdsStandard \
  --depth 2 --inheritance-scope start \
  -o tools/cdm-puml/dist/puml/std_inherit.puml
```

### 4. 批量聚合根输出
```bash
python tools/cdm-puml/generate_puml.py \
  --batch-roots \
  --batch-roots-config tools/cdm-puml/config/roots.yaml \
  --batch-roots-output tools/cdm-puml/dist \
  --depth 2
```

## 常见问题 (FAQ)

**Q: 环境只安装了 `commondatamodel.objectmodel` 或 `cdm.objectmodel` 其中之一可以吗？**  
A: 可以，`cdm_puml.compatibility` 会优先尝试 `cdm.objectmodel`，若导入失败会自动回退到 `commondatamodel.objectmodel`。

**Q: 翻译资源如何组织？**  
A: `entities.csv` 至少包含列 `domain,name,lang,label`，`attributes.csv` 包含 `domain,entity,attr,lang,label`。当主语言缺失时会尝试使用备用语言，若启用双语模式会以 `主（副）` 的形式拼接。

**Q: 如何提升大图渲染性能？**  
A: 可使用 `--hide-attributes` 降低输出体量，或通过 `--resources` 精确指定聚焦实体并控制 `--depth`。

**Q: 继承覆盖如何生效？**  
A: 在 `config/inheritance_overrides.yaml` 中按照示例配置 `add/remove/replace`，运行时通过 `--inheritance-config` 指向该文件即可。

## 输出目录

- `tools/cdm-puml/dist/puml/`：生成的 PlantUML 文件。
- `tools/cdm-puml/dist/docs/api_resources.yaml`：资源索引（若启用 `--dump-resource-index`）。

欢迎根据自身业务模型扩展脚本，并结合 PlantUML 渲染生成更丰富的文档与图谱。
