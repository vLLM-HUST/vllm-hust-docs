# vllm-hust 源码调用流程图

本文只做一件事：把前面总览和专题拆解里反复提到的关键路径，压缩成几张可用于代码导航和排障的调用流程图。

## 1. CLI `serve` 启动到引擎就绪

这张图关注的是启动期，而不是单请求执行期。

```mermaid
sequenceDiagram
    participant U as User CLI
    participant M as entrypoints/cli/main.py
    participant EU as entrypoints/utils.py
    participant AA as engine/arg_utils.py
    participant AS as openai/api_server.py
    participant AL as v1/engine/async_llm.py
    participant EC as v1/engine/core_client.py
    participant EX as v1/executor/*

    U->>M: vllm-hust serve ...
    M->>EU: cli_env_setup()
    EU->>EU: set spawn multiproc method
    EU->>EU: optional Ascend torch_npu preflight
    M->>AS: dispatch serve command
    AS->>AA: AsyncEngineArgs.from_cli_args(args)
    AA->>AA: create_engine_config()
    AA-->>AS: VllmConfig
    AS->>AL: AsyncLLM.from_vllm_config(vllm_config)
    AL->>EC: make_async_mp_client(...)
    EC->>EX: choose executor class
    EX-->>EC: engine backend ready
    EC-->>AL: EngineCore client connected
    AL-->>AS: engine client ready
```

这条链说明三个很重要的事实：

- 启动时的关键不是模型层，而是 `cli_env_setup()` 和 `create_engine_config()`。
- OpenAI 服务启动本质上是创建 `AsyncLLM` 并绑定 EngineCore 客户端。
- Executor 的选择发生在引擎创建过程中，而不是请求到来之后。

## 2. OpenAI Chat 请求调用链

这张图关注的是单次 Chat Completion 请求从 API 到引擎，再回到响应的主线。

```mermaid
sequenceDiagram
    participant C as Client
    participant API as openai/api_server.py
    participant CHAT as chat_completion/serving.py
    participant OAS as openai/engine/serving.py
    participant R as renderers + chat_utils
    participant IP as v1/engine/input_processor.py
    participant AL as v1/engine/async_llm.py
    participant EC as v1/engine/core_client.py
    participant OP as v1/engine/output_processor.py
    participant RP as reasoning parser
    participant TP as tool parser

    C->>API: POST /v1/chat/completions
    API->>CHAT: create_chat_completion(request)
    CHAT->>OAS: model and engine checks
    CHAT->>R: render_chat(request)
    R-->>CHAT: conversation + engine_prompts
    CHAT->>AL: engine client generate / stream
    AL->>IP: process_inputs(...)
    IP-->>AL: EngineCoreRequest
    AL->>EC: add_request_async(...)
    EC-->>AL: EngineCoreOutputs
    AL->>OP: convert outputs
    OP-->>CHAT: RequestOutput stream / final output
    CHAT->>RP: optional reasoning parse
    CHAT->>TP: optional tool parse
    CHAT-->>API: OpenAI-compatible response
    API-->>C: JSON or stream chunks
```

最容易读错的一点是：

- chat serving 不直接执行模型；
- 它负责渲染请求、选择 reasoning/tool parser、消费引擎输出并还原协议。

## 3. 平台激活与 Ascend 护栏流程

这张图关注的是平台路径，而不是请求路径。

```mermaid
sequenceDiagram
    participant P as Python process
    participant EO as env_override.py
    participant CLI as entrypoints/utils.py
    participant PL as platforms/__init__.py
    participant PG as plugins/__init__.py
    participant OOT as vllm.platform_plugins

    P->>EO: import vllm
    EO->>EO: detect runtime paths
    EO->>EO: maybe inject LD_LIBRARY_PATH/PATH
    EO->>EO: maybe re-exec process
    P->>CLI: cli_env_setup()
    CLI->>CLI: optional Ascend torch_npu preflight
    P->>PL: resolve current_platform
    PL->>PG: load_plugins_by_group(platform_plugins)
    PG-->>PL: discovered external platform plugins
    PL->>PL: run builtin detectors
    PL->>OOT: activate external plugin if selected
    PL-->>P: current Platform class
```

这张图强调两件事：

- 运行时环境补齐与平台选择不是同一件事；
- Ascend 相关 fork 增强更多在“启动护栏”和“插件接入”，而不是共享执行链本体。

## 4. 多模态与 AGI4S 能力调用链

这张图把多模态、reasoning 和 tool calling 放到同一张图里，看它们分别介入哪一段。

```mermaid
sequenceDiagram
    participant Req as OpenAI request
    participant Render as renderer/chat utils
    participant MM as multimodal registry
    participant IP as InputProcessor
    participant ENG as EngineCore
    participant OP as OutputProcessor
    participant Reason as reasoning parser
    participant Tool as tool parser
    participant Resp as OpenAI response

    Req->>Render: build prompt and template context
    Render->>MM: preprocess multimodal content
    MM-->>Render: normalized multimodal inputs
    Render->>IP: final prompt + params + modality data
    IP->>ENG: EngineCoreRequest
    ENG-->>OP: raw outputs
    OP->>Reason: parse reasoning if enabled
    OP->>Tool: parse tool calls if enabled
    Reason-->>Resp: reasoning-aware content
    Tool-->>Resp: structured tool calls
```

它说明：

- 多模态主要介入输入侧。
- reasoning 和 tool calling 主要介入输出解释侧。
- OpenAI 响应层只是把这些模块的结果重新打包给客户端。

## 5. 用流程图排障时怎么选图

### 服务启动失败

先看“CLI `serve` 启动到引擎就绪”。

### 请求到了但没生成

先看“OpenAI Chat 请求调用链”。

### Ascend 环境反复出问题

先看“平台激活与 Ascend 护栏流程”。

### 多模态、reasoning、tool use 行为不对

先看“多模态与 AGI4S 能力调用链”。

## 6. 一句话总结

这些图想传达的不是“调用很多”，而是“每类问题其实都能被定位到少数几个清晰边界”：

- 启动护栏边界
- 配置收敛边界
- 引擎编排边界
- 平台插件边界
- 多模态与 AGI4S 横切能力边界

只要沿这些边界读代码，`vllm-hust` 的复杂度会下降很多。