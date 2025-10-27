# Common Data Model（CDM）学习与扩展指南

> 本文档旨在帮助企业数据架构师和开发者快速理解 CDM 的核心概念、仓库结构以及如何将标准 schema 转换、扩展并融合到自有企业数据模型中，同时提供自动生成 PlantUML 视图的示例脚本以加速理解。

## 1. 项目概览

- **CDM 的定位**：CDM 提供一套声明式的、可扩展的业务实体定义，覆盖销售、服务、市场、财务、运营等场景，目标是让数据和应用在多渠道、多供应商之间无缝互通，并通过自描述的结构与语义帮助应用理解数据。 【F:README.md†L16-L31】
- **仓库使用方式**：可以通过 `schemaDocuments` 下的实体索引或在线的可视化实体导航器探索各业务领域的实体、继承关系及属性。 【F:README.md†L36-L41】
- **版本策略**：CDM 采用“只新增不破坏”的版本策略，避免对既有实体和属性进行强制性变更，从而保障升级的可持续性。 【F:README.md†L43-L49】
- **SDK 更新提醒**：自 1.7.1 版起，SDK 已内置基础定义但不包含特定行业 schema，如需依赖请从仓库打包引用；旧版 SDK 需尽快升级以避免 Schema Store 下线带来的影响。 【F:README.md†L1-L5】

## 2. 仓库结构与推荐学习路线

1. **了解基础定义**：首先阅读 `schemaDocuments/cdmfoundation/cdmfoundation.manifest.cdm.json`，它列出了基础文档、实体以及引用文件，是所有领域 schema 的根基。 【F:schemaDocuments/cdmfoundation/cdmfoundation.manifest.cdm.json†L1-L146】
2. **研究核心业务实体**：进入 `schemaDocuments/core`，如 `applicationCommon` 中的 `Account.cdm.json` 展示了完整实体定义、继承关系、属性分组与 trait 的使用方式。 【F:schemaDocuments/core/applicationCommon/Account.cdm.json†L1-L200】
3. **选择对应语言 SDK**：根据企业技术栈选择 C#/Java/Python/TypeScript SDK，以便在代码层面操作 CDM 元数据。例如 TypeScript SDK 需要 Node.js 与 PowerShell 环境，提供 `npm ci`、`npm run build`、`npm run test` 等命令；Python SDK 提供 `pip3 install -r requirements.txt`、`python -m unittest` 等操作指导。 【F:objectModel/TypeScript/README.md†L1-L47】【F:objectModel/Python/README.md†L1-L29】

> 建议按照“基础 -> 核心实体 -> SDK 实践 -> 行业扩展”的顺序学习，并结合自身数据域逐步映射。

## 3. 理解 CDM Schema 的关键要素

### 3.1 Manifest（清单）
- Manifest 使用 `jsonSchemaSemanticVersion`、`documentVersion` 等字段描述版本信息，并通过 `imports` 引入共享文档（如 `primitives.cdm.json`）。
- `exhibitsTraits` 中的 `has.fileList` trait 提供 manifest 所包含的文档清单，便于自动化脚本发现资源。 【F:schemaDocuments/cdmfoundation/cdmfoundation.manifest.cdm.json†L1-L77】
- `entities` 段列出当前 manifest 包含的本地实体及其对应的文档路径，是解析实体定义的入口。 【F:schemaDocuments/cdmfoundation/cdmfoundation.manifest.cdm.json†L84-L146】

### 3.2 实体定义
- 实体通常通过 `extendsEntity` 继承标准基类（如 `CdsStandard`），并通过 `exhibitsTraits` 指定显示名称、描述、版本等元信息。 【F:schemaDocuments/core/applicationCommon/Account.cdm.json†L10-L55】
- 属性分布在 `hasAttributes` 中，可使用 `attributeGroupReference` 分组；每个属性包含目的（`purpose`）、数据类型（`dataType`/`dataTypeReference`）、本地化显示和描述等 trait。 【F:schemaDocuments/core/applicationCommon/Account.cdm.json†L56-L188】
- 通过 `resolutionGuidance` 可以定义推导属性（如 `_display` 字段）以支持本地化显示或枚举映射。 【F:schemaDocuments/core/applicationCommon/Account.cdm.json†L189-L200】

### 3.3 Trait 与数据类型
- 常见 trait 如 `is.requiredAtLevel`、`is.localized.displayedAs`、`is.localized.describedAs` 可表达业务约束与多语言文案。 【F:schemaDocuments/core/applicationCommon/Account.cdm.json†L65-L187】
- `listLookup` 等数据类型可结合 `constantValues` 定义枚举值列表，便于生成 UI 选项或数据验证。 【F:schemaDocuments/core/applicationCommon/Account.cdm.json†L114-L145】

## 4. 将 CDM 融合到企业数据模型

1. **建立概念映射**：以企业现有的主题域为切入点，将 CDM 实体（如 Account）与内部概念对齐，记录继承链与 trait 以保持语义一致。
2. **属性对照与扩展**：使用 `hasAttributes` 中的 trait 描述来理解字段含义，并根据企业需要新增属性或 trait，确保不破坏原有定义的可选/必填约束。 【F:schemaDocuments/core/applicationCommon/Account.cdm.json†L56-L187】
3. **版本管理**：遵循 manifest 中的版本字段与 README 中的“只新增不破坏”策略，对扩展 schema 采用增量版本号，避免对上游依赖造成影响。 【F:README.md†L43-L49】【F:schemaDocuments/cdmfoundation/cdmfoundation.manifest.cdm.json†L1-L13】
4. **包装行业扩展**：由于 SDK 仅内置基础定义，行业或自定义 schema 需要和项目一起打包发布，在部署时显式指定检索路径。 【F:README.md†L1-L5】

## 5. Schema 转换与治理实践

- **清单驱动的解析**：基于 manifest 的 `has.fileList` trait 自动收集所需的 `.cdm.json` 文件，再按 `entities` 列表逐个解析，这也是后续脚本自动化的基础。 【F:schemaDocuments/cdmfoundation/cdmfoundation.manifest.cdm.json†L15-L146】
- **字段标准化**：借助属性中的 `sourceName`、`displayName`、`description` 信息，建立企业内部命名规范与数据字典，实现从 CDM 到内部模型的字段映射。 【F:schemaDocuments/core/applicationCommon/Account.cdm.json†L108-L193】
- **枚举与主数据处理**：利用 `listLookup` 的 `constantValues` 直接生成主数据表或校验规则；若企业已有主数据系统，可将这些值映射到统一编码。 【F:schemaDocuments/core/applicationCommon/Account.cdm.json†L114-L145】
- **继承关系落地**：`extendsEntity` 信息可转化为企业模型的继承或实体关系图，在整合时保留父实体的公共字段，减少重复定义。 【F:schemaDocuments/core/applicationCommon/Account.cdm.json†L10-L55】

## 6. 利用脚本生成 PlantUML 视图

仓库新增的 `samples/plantuml/generate_plantuml.py` 提供一个轻量级示例，展示如何基于 manifest 自动生成 PlantUML 类图：

```bash
python samples/plantuml/generate_plantuml.py schemaDocuments/cdmfoundation/cdmfoundation.manifest.cdm.json --entities Account --output Account.puml
```

- 脚本会读取 manifest，解析本地实体，提取属性和继承关系，并输出包含属性描述的 PlantUML 代码。 【F:samples/plantuml/generate_plantuml.py†L1-L127】
- 支持通过 `--entities` 参数筛选特定实体，若未指定则生成清单中的全部本地实体。 【F:samples/plantuml/generate_plantuml.py†L88-L107】【F:samples/plantuml/generate_plantuml.py†L130-L147】
- 输出可直接粘贴到 PlantUML 渲染器或集成到企业文档自动化流程中，实现 CDM 模型的可视化审查。

## 7. 进一步的自动化建议

- **多语言支持**：脚本示例展示了如何优先使用 trait 中的本地化描述，可扩展为根据企业语言偏好生成多份图谱。 【F:samples/plantuml/generate_plantuml.py†L67-L85】
- **跨团队协作**：结合 TypeScript/Python SDK，可在数据治理平台中加载 CDM 模型、比对差异并生成合并策略。 【F:objectModel/TypeScript/README.md†L1-L47】【F:objectModel/Python/README.md†L1-L29】
- **合规与版本控制**：依托 README 的版本策略，建议在企业 Git 仓库中维护扩展 schema，并通过自动化脚本生成 PlantUML 及数据字典，供评审与审计使用。 【F:README.md†L43-L49】

---
通过以上步骤，您可以快速建立对 CDM 的系统认知，制定与企业数据模型的映射策略，并借助脚本化方式持续生成可视化文档，加速团队对模型的理解与落地实施。
