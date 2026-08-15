---
title: "AI and Copilot Features"
chapter: 29
source_url: "https://deepwiki.com/microsoft/vscode/7-ai-and-copilot-features"
word_count: 1202
mermaid_diagrams: 2
---

# AI and Copilot Features

<details>
<summary>Relevant source files</summary>

The following files were used as context for generating this wiki page:

- [extensions/copilot/package.json](extensions/copilot/package.json)
- [extensions/copilot/package.nls.json](extensions/copilot/package.nls.json)
- [extensions/copilot/src/extension/chatSessions/common/chatSessionMetadataStore.ts](extensions/copilot/src/extension/chatSessions/common/chatSessionMetadataStore.ts)
- [extensions/copilot/src/extension/chatSessions/common/chatSessionWorkspaceFolderService.ts](extensions/copilot/src/extension/chatSessions/common/chatSessionWorkspaceFolderService.ts)
- [extensions/copilot/src/extension/chatSessions/common/chatSessionWorktreeCheckpointService.ts](extensions/copilot/src/extension/chatSessions/common/chatSessionWorktreeCheckpointService.ts)
- [extensions/copilot/src/extension/chatSessions/common/chatSessionWorktreeService.ts](extensions/copilot/src/extension/chatSessions/common/chatSessionWorktreeService.ts)
- [extensions/copilot/src/extension/chatSessions/common/folderRepositoryManager.ts](extensions/copilot/src/extension/chatSessions/common/folderRepositoryManager.ts)
- [extensions/copilot/src/extension/chatSessions/common/test/mockChatSessionMetadataStore.ts](extensions/copilot/src/extension/chatSessions/common/test/mockChatSessionMetadataStore.ts)
- [extensions/copilot/src/extension/chatSessions/copilotcli/common/copilotCLITools.ts](extensions/copilot/src/extension/chatSessions/copilotcli/common/copilotCLITools.ts)
- [extensions/copilot/src/extension/chatSessions/copilotcli/common/test/copilotCLITools.spec.ts](extensions/copilot/src/extension/chatSessions/copilotcli/common/test/copilotCLITools.spec.ts)
- [extensions/copilot/src/extension/chatSessions/copilotcli/node/copilotCli.ts](extensions/copilot/src/extension/chatSessions/copilotcli/node/copilotCli.ts)
- [extensions/copilot/src/extension/chatSessions/copilotcli/node/copilotcliSession.ts](extensions/copilot/src/extension/chatSessions/copilotcli/node/copilotcliSession.ts)
- [extensions/copilot/src/extension/chatSessions/copilotcli/node/copilotcliSessionService.ts](extensions/copilot/src/extension/chatSessions/copilotcli/node/copilotcliSessionService.ts)
- [extensions/copilot/src/extension/chatSessions/copilotcli/node/permissionHelpers.ts](extensions/copilot/src/extension/chatSessions/copilotcli/node/permissionHelpers.ts)
- [extensions/copilot/src/extension/chatSessions/copilotcli/node/test/copilotCliModels.spec.ts](extensions/copilot/src/extension/chatSessions/copilotcli/node/test/copilotCliModels.spec.ts)
- [extensions/copilot/src/extension/chatSessions/copilotcli/node/test/copilotCliSessionService.spec.ts](extensions/copilot/src/extension/chatSessions/copilotcli/node/test/copilotCliSessionService.spec.ts)
- [extensions/copilot/src/extension/chatSessions/copilotcli/node/test/copilotcliSession.spec.ts](extensions/copilot/src/extension/chatSessions/copilotcli/node/test/copilotcliSession.spec.ts)
- [extensions/copilot/src/extension/chatSessions/copilotcli/node/test/permissionHelpers.spec.ts](extensions/copilot/src/extension/chatSessions/copilotcli/node/test/permissionHelpers.spec.ts)
- [extensions/copilot/src/extension/chatSessions/copilotcli/node/test/testHelpers.ts](extensions/copilot/src/extension/chatSessions/copilotcli/node/test/testHelpers.ts)
- [extensions/copilot/src/extension/chatSessions/vscode-node/chatSessionWorkspaceFolderServiceImpl.ts](extensions/copilot/src/extension/chatSessions/vscode-node/chatSessionWorkspaceFolderServiceImpl.ts)
- [extensions/copilot/src/extension/chatSessions/vscode-node/chatSessionWorktreeCheckpointServiceImpl.ts](extensions/copilot/src/extension/chatSessions/vscode-node/chatSessionWorktreeCheckpointServiceImpl.ts)
- [extensions/copilot/src/extension/chatSessions/vscode-node/chatSessionWorktreeServiceImpl.ts](extensions/copilot/src/extension/chatSessions/vscode-node/chatSessionWorktreeServiceImpl.ts)
- [extensions/copilot/src/extension/chatSessions/vscode-node/chatSessions.ts](extensions/copilot/src/extension/chatSessions/vscode-node/chatSessions.ts)
- [extensions/copilot/src/extension/chatSessions/vscode-node/copilotCLIChatSessions.ts](extensions/copilot/src/extension/chatSessions/vscode-node/copilotCLIChatSessions.ts)
- [extensions/copilot/src/extension/chatSessions/vscode-node/copilotCLIChatSessionsContribution.ts](extensions/copilot/src/extension/chatSessions/vscode-node/copilotCLIChatSessionsContribution.ts)
- [extensions/copilot/src/extension/chatSessions/vscode-node/copilotCLIModelDetails.ts](extensions/copilot/src/extension/chatSessions/vscode-node/copilotCLIModelDetails.ts)
- [extensions/copilot/src/extension/chatSessions/vscode-node/folderRepositoryManagerImpl.ts](extensions/copilot/src/extension/chatSessions/vscode-node/folderRepositoryManagerImpl.ts)
- [extensions/copilot/src/extension/chatSessions/vscode-node/sessionOptionGroupBuilder.ts](extensions/copilot/src/extension/chatSessions/vscode-node/sessionOptionGroupBuilder.ts)
- [extensions/copilot/src/extension/chatSessions/vscode-node/test/chatSessionWorkspaceFolderService.spec.ts](extensions/copilot/src/extension/chatSessions/vscode-node/test/chatSessionWorkspaceFolderService.spec.ts)
- [extensions/copilot/src/extension/chatSessions/vscode-node/test/copilotCLIChatSessionParticipant.spec.ts](extensions/copilot/src/extension/chatSessions/vscode-node/test/copilotCLIChatSessionParticipant.spec.ts)
- [extensions/copilot/src/extension/chatSessions/vscode-node/test/copilotCLIChatSessions.spec.ts](extensions/copilot/src/extension/chatSessions/vscode-node/test/copilotCLIChatSessions.spec.ts)
- [extensions/copilot/src/extension/chatSessions/vscode-node/test/copilotCLIModelDetails.spec.ts](extensions/copilot/src/extension/chatSessions/vscode-node/test/copilotCLIModelDetails.spec.ts)
- [extensions/copilot/src/extension/chatSessions/vscode-node/test/folderRepositoryManager.spec.ts](extensions/copilot/src/extension/chatSessions/vscode-node/test/folderRepositoryManager.spec.ts)
- [extensions/copilot/src/extension/chatSessions/vscode-node/test/sessionOptionGroupBuilder.spec.ts](extensions/copilot/src/extension/chatSessions/vscode-node/test/sessionOptionGroupBuilder.spec.ts)
- [extensions/copilot/src/platform/configuration/common/configurationService.ts](extensions/copilot/src/platform/configuration/common/configurationService.ts)
- [extensions/copilot/src/platform/git/vscode-node/utils.ts](extensions/copilot/src/platform/git/vscode-node/utils.ts)
- [extensions/copilot/test/e2e/cli.stest.ts](extensions/copilot/test/e2e/cli.stest.ts)
- [src/vs/platform/agentHost/common/agentModelPricing.ts](src/vs/platform/agentHost/common/agentModelPricing.ts)
- [src/vs/platform/agentHost/common/agentModelSource.ts](src/vs/platform/agentHost/common/agentModelSource.ts)
- [src/vs/platform/agentHost/common/agentService.ts](src/vs/platform/agentHost/common/agentService.ts)
- [src/vs/platform/agentHost/common/claudeProviders.ts](src/vs/platform/agentHost/common/claudeProviders.ts)
- [src/vs/platform/agentHost/common/state/sessionState.ts](src/vs/platform/agentHost/common/state/sessionState.ts)
- [src/vs/platform/agentHost/node/agentHostStateManager.ts](src/vs/platform/agentHost/node/agentHostStateManager.ts)
- [src/vs/platform/agentHost/node/agentService.ts](src/vs/platform/agentHost/node/agentService.ts)
- [src/vs/platform/agentHost/node/agentSideEffects.ts](src/vs/platform/agentHost/node/agentSideEffects.ts)
- [src/vs/platform/agentHost/node/copilot/copilotAgent.ts](src/vs/platform/agentHost/node/copilot/copilotAgent.ts)
- [src/vs/platform/agentHost/node/copilot/copilotAgentSession.ts](src/vs/platform/agentHost/node/copilot/copilotAgentSession.ts)
- [src/vs/platform/agentHost/test/node/agentHostStateManager.test.ts](src/vs/platform/agentHost/test/node/agentHostStateManager.test.ts)
- [src/vs/platform/agentHost/test/node/agentService.test.ts](src/vs/platform/agentHost/test/node/agentService.test.ts)
- [src/vs/platform/agentHost/test/node/agentSideEffects.test.ts](src/vs/platform/agentHost/test/node/agentSideEffects.test.ts)
- [src/vs/platform/agentHost/test/node/claudeModelSelection.test.ts](src/vs/platform/agentHost/test/node/claudeModelSelection.test.ts)
- [src/vs/platform/agentHost/test/node/copilotAgent.test.ts](src/vs/platform/agentHost/test/node/copilotAgent.test.ts)
- [src/vs/platform/agentHost/test/node/copilotAgentSession.test.ts](src/vs/platform/agentHost/test/node/copilotAgentSession.test.ts)
- [src/vs/platform/agentHost/test/node/mockAgent.ts](src/vs/platform/agentHost/test/node/mockAgent.ts)
- [src/vs/sessions/contrib/providers/agentHost/browser/openSubagentChat.ts](src/vs/sessions/contrib/providers/agentHost/browser/openSubagentChat.ts)
- [src/vs/sessions/contrib/providers/agentHost/test/browser/openSubagentChat.test.ts](src/vs/sessions/contrib/providers/agentHost/test/browser/openSubagentChat.test.ts)
- [src/vs/workbench/contrib/chat/browser/actions/chatActions.ts](src/vs/workbench/contrib/chat/browser/actions/chatActions.ts)
- [src/vs/workbench/contrib/chat/browser/actions/chatExecuteActions.ts](src/vs/workbench/contrib/chat/browser/actions/chatExecuteActions.ts)
- [src/vs/workbench/contrib/chat/browser/agentSessions/agentHost/agentHostChatContribution.ts](src/vs/workbench/contrib/chat/browser/agentSessions/agentHost/agentHostChatContribution.ts)
- [src/vs/workbench/contrib/chat/browser/agentSessions/agentHost/agentHostLanguageModelProvider.ts](src/vs/workbench/contrib/chat/browser/agentSessions/agentHost/agentHostLanguageModelProvider.ts)
- [src/vs/workbench/contrib/chat/browser/agentSessions/agentHost/agentHostSessionHandler.ts](src/vs/workbench/contrib/chat/browser/agentSessions/agentHost/agentHostSessionHandler.ts)
- [src/vs/workbench/contrib/chat/browser/agentSessions/agentHost/agentHostSessionListController.ts](src/vs/workbench/contrib/chat/browser/agentSessions/agentHost/agentHostSessionListController.ts)
- [src/vs/workbench/contrib/chat/browser/agentSessions/agentHost/stateToProgressAdapter.ts](src/vs/workbench/contrib/chat/browser/agentSessions/agentHost/stateToProgressAdapter.ts)
- [src/vs/workbench/contrib/chat/browser/agentSessions/localAgentSessionsController.ts](src/vs/workbench/contrib/chat/browser/agentSessions/localAgentSessionsController.ts)
- [src/vs/workbench/contrib/chat/browser/chat.contribution.ts](src/vs/workbench/contrib/chat/browser/chat.contribution.ts)
- [src/vs/workbench/contrib/chat/browser/chat.ts](src/vs/workbench/contrib/chat/browser/chat.ts)
- [src/vs/workbench/contrib/chat/browser/widget/chatContentParts/chatDisabledClaudeHooksContentPart.ts](src/vs/workbench/contrib/chat/browser/widget/chatContentParts/chatDisabledClaudeHooksContentPart.ts)
- [src/vs/workbench/contrib/chat/browser/widget/chatContentParts/chatHookContentPart.ts](src/vs/workbench/contrib/chat/browser/widget/chatContentParts/chatHookContentPart.ts)
- [src/vs/workbench/contrib/chat/browser/widget/chatContentParts/chatMcpServersInteractionContentPart.ts](src/vs/workbench/contrib/chat/browser/widget/chatContentParts/chatMcpServersInteractionContentPart.ts)
- [src/vs/workbench/contrib/chat/browser/widget/chatContentParts/chatProgressContentPart.ts](src/vs/workbench/contrib/chat/browser/widget/chatContentParts/chatProgressContentPart.ts)
- [src/vs/workbench/contrib/chat/browser/widget/chatContentParts/chatSubagentContentPart.ts](src/vs/workbench/contrib/chat/browser/widget/chatContentParts/chatSubagentContentPart.ts)
- [src/vs/workbench/contrib/chat/browser/widget/chatContentParts/chatTaskContentPart.ts](src/vs/workbench/contrib/chat/browser/widget/chatContentParts/chatTaskContentPart.ts)
- [src/vs/workbench/contrib/chat/browser/widget/chatContentParts/chatThinkingContentPart.ts](src/vs/workbench/contrib/chat/browser/widget/chatContentParts/chatThinkingContentPart.ts)
- [src/vs/workbench/contrib/chat/browser/widget/chatContentParts/media/chatCodeBlockPill.css](src/vs/workbench/contrib/chat/browser/widget/chatContentParts/media/chatCodeBlockPill.css)
- [src/vs/workbench/contrib/chat/browser/widget/chatContentParts/media/chatDisabledClaudeHooksContent.css](src/vs/workbench/contrib/chat/browser/widget/chatContentParts/media/chatDisabledClaudeHooksContent.css)
- [src/vs/workbench/contrib/chat/browser/widget/chatContentParts/media/chatHookContentPart.css](src/vs/workbench/contrib/chat/browser/widget/chatContentParts/media/chatHookContentPart.css)
- [src/vs/workbench/contrib/chat/browser/widget/chatContentParts/media/chatSubagentContent.css](src/vs/workbench/contrib/chat/browser/widget/chatContentParts/media/chatSubagentContent.css)
- [src/vs/workbench/contrib/chat/browser/widget/chatContentParts/media/chatThinkingContent.css](src/vs/workbench/contrib/chat/browser/widget/chatContentParts/media/chatThinkingContent.css)
- [src/vs/workbench/contrib/chat/browser/widget/chatContentParts/toolInvocationParts/chatResultListSubPart.ts](src/vs/workbench/contrib/chat/browser/widget/chatContentParts/toolInvocationParts/chatResultListSubPart.ts)
- [src/vs/workbench/contrib/chat/browser/widget/chatContentParts/toolInvocationParts/chatToolInvocationSubPart.ts](src/vs/workbench/contrib/chat/browser/widget/chatContentParts/toolInvocationParts/chatToolInvocationSubPart.ts)
- [src/vs/workbench/contrib/chat/browser/widget/chatContentParts/toolInvocationParts/chatToolProgressPart.ts](src/vs/workbench/contrib/chat/browser/widget/chatContentParts/toolInvocationParts/chatToolProgressPart.ts)
- [src/vs/workbench/contrib/chat/browser/widget/chatContentParts/toolInvocationParts/chatToolStreamingSubPart.ts](src/vs/workbench/contrib/chat/browser/widget/chatContentParts/toolInvocationParts/chatToolStreamingSubPart.ts)
- [src/vs/workbench/contrib/chat/browser/widget/chatListRenderer.ts](src/vs/workbench/contrib/chat/browser/widget/chatListRenderer.ts)
- [src/vs/workbench/contrib/chat/browser/widget/chatWidget.ts](src/vs/workbench/contrib/chat/browser/widget/chatWidget.ts)
- [src/vs/workbench/contrib/chat/browser/widget/input/chatInputPart.ts](src/vs/workbench/contrib/chat/browser/widget/input/chatInputPart.ts)
- [src/vs/workbench/contrib/chat/browser/widget/media/chat.css](src/vs/workbench/contrib/chat/browser/widget/media/chat.css)
- [src/vs/workbench/contrib/chat/common/actions/chatContextKeys.ts](src/vs/workbench/contrib/chat/common/actions/chatContextKeys.ts)
- [src/vs/workbench/contrib/chat/common/chatService/chatService.ts](src/vs/workbench/contrib/chat/common/chatService/chatService.ts)
- [src/vs/workbench/contrib/chat/common/chatService/chatServiceImpl.ts](src/vs/workbench/contrib/chat/common/chatService/chatServiceImpl.ts)
- [src/vs/workbench/contrib/chat/common/constants.ts](src/vs/workbench/contrib/chat/common/constants.ts)
- [src/vs/workbench/contrib/chat/common/model/chatModel.ts](src/vs/workbench/contrib/chat/common/model/chatModel.ts)
- [src/vs/workbench/contrib/chat/common/model/chatSessionOperationLog.ts](src/vs/workbench/contrib/chat/common/model/chatSessionOperationLog.ts)
- [src/vs/workbench/contrib/chat/common/model/chatViewModel.ts](src/vs/workbench/contrib/chat/common/model/chatViewModel.ts)
- [src/vs/workbench/contrib/chat/common/widget/annotations.ts](src/vs/workbench/contrib/chat/common/widget/annotations.ts)
- [src/vs/workbench/contrib/chat/test/browser/agentSessions/agentHostChatContribution.test.ts](src/vs/workbench/contrib/chat/test/browser/agentSessions/agentHostChatContribution.test.ts)
- [src/vs/workbench/contrib/chat/test/browser/agentSessions/agentHostClientTools.test.ts](src/vs/workbench/contrib/chat/test/browser/agentSessions/agentHostClientTools.test.ts)
- [src/vs/workbench/contrib/chat/test/browser/agentSessions/agentHostLanguageModelProvider.test.ts](src/vs/workbench/contrib/chat/test/browser/agentSessions/agentHostLanguageModelProvider.test.ts)
- [src/vs/workbench/contrib/chat/test/browser/agentSessions/localAgentSessionsController.test.ts](src/vs/workbench/contrib/chat/test/browser/agentSessions/localAgentSessionsController.test.ts)
- [src/vs/workbench/contrib/chat/test/browser/agentSessions/stateToProgressAdapter.test.ts](src/vs/workbench/contrib/chat/test/browser/agentSessions/stateToProgressAdapter.test.ts)
- [src/vs/workbench/contrib/chat/test/browser/widget/chatContentParts/chatSubagentContentPart.test.ts](src/vs/workbench/contrib/chat/test/browser/widget/chatContentParts/chatSubagentContentPart.test.ts)
- [src/vs/workbench/contrib/chat/test/browser/widget/chatContentParts/chatThinkingContentPart.test.ts](src/vs/workbench/contrib/chat/test/browser/widget/chatContentParts/chatThinkingContentPart.test.ts)
- [src/vs/workbench/contrib/chat/test/browser/widget/chatListRenderer.test.ts](src/vs/workbench/contrib/chat/test/browser/widget/chatListRenderer.test.ts)
- [src/vs/workbench/contrib/chat/test/common/chatService/__snapshots__/ChatService_can_deserialize.0.snap](src/vs/workbench/contrib/chat/test/common/chatService/__snapshots__/ChatService_can_deserialize.0.snap)
- [src/vs/workbench/contrib/chat/test/common/chatService/__snapshots__/ChatService_can_deserialize_with_response.0.snap](src/vs/workbench/contrib/chat/test/common/chatService/__snapshots__/ChatService_can_deserialize_with_response.0.snap)
- [src/vs/workbench/contrib/chat/test/common/chatService/__snapshots__/ChatService_can_serialize.1.snap](src/vs/workbench/contrib/chat/test/common/chatService/__snapshots__/ChatService_can_serialize.1.snap)
- [src/vs/workbench/contrib/chat/test/common/chatService/__snapshots__/ChatService_sendRequest_fails.0.snap](src/vs/workbench/contrib/chat/test/common/chatService/__snapshots__/ChatService_sendRequest_fails.0.snap)
- [src/vs/workbench/contrib/chat/test/common/chatService/chatService.test.ts](src/vs/workbench/contrib/chat/test/common/chatService/chatService.test.ts)
- [src/vs/workbench/contrib/chat/test/common/chatService/mockChatService.ts](src/vs/workbench/contrib/chat/test/common/chatService/mockChatService.ts)
- [src/vs/workbench/contrib/chat/test/common/model/chatModel.test.ts](src/vs/workbench/contrib/chat/test/common/model/chatModel.test.ts)
- [src/vs/workbench/contrib/chat/test/common/widget/annotations.test.ts](src/vs/workbench/contrib/chat/test/common/widget/annotations.test.ts)

</details>



The AI and Copilot subsystem in VS Code provides a comprehensive framework for integrating Large Language Models (LLMs) into the development workflow. This includes the primary Chat UI, inline code completions, agent-based orchestration, and deep integration with the GitHub Copilot extension. The architecture is designed to be provider-agnostic, supporting multiple models and interaction modes while maintaining a consistent user experience across the workbench and external interfaces.

### Core Architecture Overview

The AI features are built on a multi-layered service architecture that separates UI components from the underlying model logic, agent execution, and session management.

1.  **UI Layer**: Centered around the `ChatWidget` and `InlineChatWidget`, providing the visual interface for user interaction [src/vs/workbench/contrib/chat/browser/chat.ts:69-75]().
2.  **Service Layer**: Managed by `IChatService`, which handles session lifecycles, request queuing, and streaming responses [src/vs/workbench/contrib/chat/common/chatService/chatService.ts:58-59]().
3.  **Model Layer**: Implemented via `ChatModel` and `ChatViewModel`, which maintain the state of conversations and their visual representation [src/vs/workbench/contrib/chat/common/model/chatModel.ts:56-57]() [src/vs/workbench/contrib/chat/common/model/chatViewModel.ts:61-62]().
4.  **Extension Layer**: The GitHub Copilot extension (`copilot-chat`) contributes specific agents, tools (like `copilot_searchCodebase`), and orchestration logic [extensions/copilot/package.json:1-180]().
5.  **Agent Host Platform**: A dedicated execution environment for agents (`CopilotAgent`) that allows for complex reasoning and tool use outside the main extension host [src/vs/platform/agentHost/node/copilot/copilotAgent.ts:45-45]().

### Feature Areas

#### Chat Service and Widget
The primary interface for AI interaction. It supports various `ChatModeKind` values such as `Ask`, `Edit`, and `Agent` [src/vs/workbench/contrib/chat/common/constants.ts:63-63](). The `ChatWidget` manages complex rendering of response parts via the `ChatInputPart` [src/vs/workbench/contrib/chat/browser/widget/input/chatInputPart.ts:83-83]() and `ChatListRenderer`. Response content can include specialized parts like `chatThinkingContentPart` for model reasoning [src/vs/workbench/contrib/chat/browser/widget/chatContentParts/chatThinkingContentPart.ts:1-10]() and `IChatToolInvocation` for tool progress [src/vs/workbench/contrib/chat/common/chatService/chatService.ts:59-59]().
For details, see [Chat Service and Widget](#7.1).

#### Chat Editing and Agent Sessions
Enables the AI to perform multi-file edits through `ChatEditingSession`. It includes logic for managing undo/redo of AI-generated changes, prompting the user via `IDialogService` if edits are about to be removed during a session rollback [src/vs/workbench/contrib/chat/browser/actions/chatExecuteActions.ts:90-117](). It also supports `AgentSessionProviders` to target specific execution environments like local or remote hosts [src/vs/workbench/contrib/chat/browser/actions/chatExecuteActions.ts:37-37]().
For details, see [Chat Editing and Agent Sessions](#7.2).

#### Inline Chat
Provides an "in-situ" chat experience directly within the editor. It manages interactive sessions tied to specific code ranges and is integrated via the `InlineChatController`. It allows for ghost text and inline completions to be proposed by AI [extensions/copilot/package.json:132-132]().
For details, see [Inline Chat](#7.3).

#### Copilot Extension: Agent Orchestration
The GitHub Copilot extension orchestrates complex tasks using the `AgentIntent` and `ToolCallingLoop`. It uses `AgentPrompt` (based on `prompt-tsx`) to construct context-rich prompts and manages conversation history compaction via `SummarizedConversationHistory`. It routes requests to various models including Claude, GPT, and Gemini based on capability requirements.
For details, see [Copilot Extension: Agent Orchestration](#7.4).

#### Copilot CLI and Cloud Sessions
Handles AI sessions outside the primary workbench, including CLI interactions via `CopilotCLIChatSessionsContribution` [extensions/copilot/src/extension/chatSessions/vscode-node/copilotCLIChatSessionsContribution.ts:1-52]() and synchronization with GitHub cloud-based chat history via the `CopilotCloudSessionsProvider` [extensions/copilot/src/extension/chatSessions/vscode-node/copilotCloudSessionsProvider.ts:1-59]().
For details, see [Copilot CLI and Cloud Sessions](#7.5).

#### Prompt Syntax and Custom Instructions
Manages how prompts are constructed and discovered. This includes support for prompt files (`.prompt`) [extensions/copilot/package.json:145-145]() and automatic instruction computation based on workspace context via `IPromptsService` [extensions/copilot/src/extension/chatSessions/vscode-node/copilotCLIChatSessionsContribution.ts:23-23]().
For details, see [Prompt Syntax and Custom Instructions](#7.6).

#### MCP (Model Context Protocol) Integration
Integrates the Model Context Protocol to allow VS Code to connect to external tool servers. This is managed via `mcpServerDefinitions` [extensions/copilot/package.json:146-146]() and allows agents to discover and invoke tools defined in external MCP servers using `MCPService`.
For details, see [MCP (Model Context Protocol) Integration](#7.7).

#### Agent Host Platform
The low-level platform infrastructure that hosts agents. It manages the connection and state synchronization via `CopilotAgent` [src/vs/platform/agentHost/node/copilot/copilotAgent.ts:6-45](). It handles the communication protocol and execution environment for subagents like the `execution_subagent` [extensions/copilot/package.json:182-187]().
For details, see [Agent Host Platform](#7.8).

### AI Data Flow and Orchestration

The following diagram illustrates how a user request flows from the UI through the orchestration layer to the LLM and back as structured tools and edits.

**Chat Request and Tool Execution Flow**
```mermaid
graph TD
    subgraph NaturalLanguageSpace_UI ["NaturalLanguageSpace (UI)"]
        User_Input["User Input"] --> ChatInputPart["ChatInputPart"]
        ChatInputPart["ChatInputPart"] --> ChatWidget["ChatWidget"]
    end

    subgraph CodeEntitySpace_Workbench ["CodeEntitySpace (Workbench)"]
        ChatWidget["ChatWidget"] --> IChatService_ChatServiceImpl["IChatService (ChatServiceImpl)"]
        IChatService_ChatServiceImpl["IChatService (ChatServiceImpl)"] --> ChatModel_Session_State["ChatModel (Session State)"]
        IChatService_ChatServiceImpl["IChatService (ChatServiceImpl)"] --> IChatAgentService["IChatAgentService"]
    end

    subgraph Orchestration_Agent_Host ["Orchestration (Agent Host)"]
        IChatAgentService["IChatAgentService"] --> AgentIntent_ToolCallingLoop["AgentIntent / ToolCallingLoop"]
        AgentIntent_ToolCallingLoop["AgentIntent / ToolCallingLoop"] --> AgentPrompt_prompt_tsx["AgentPrompt (prompt-tsx)"]
        AgentPrompt_prompt_tsx["AgentPrompt (prompt-tsx)"] --> LLM_Claude_GPT_Gemini["LLM (Claude / GPT / Gemini)"]
    end

    subgraph ActionSpace ["ActionSpace"]
        LLM_Claude_GPT_Gemini["LLM (Claude / GPT / Gemini)"] --> Tool_Invocation_e_g_copilot_searchCodeba["Tool Invocation (e.g., copilot_searchCodebase)"]
        Tool_Invocation_e_g_copilot_searchCodeba["Tool Invocation (e.g., copilot_searchCodebase)"] --> IFileService_SCM["IFileService / SCM"]
        LLM_Claude_GPT_Gemini["LLM (Claude / GPT / Gemini)"] --> ChatEditingSession_File_Edits["ChatEditingSession (File Edits)"]
    end

    IFileService_SCM["IFileService / SCM"] --> IChatService_ChatServiceImpl["IChatService (ChatServiceImpl)"]
    ChatEditingSession_File_Edits["ChatEditingSession (File Edits)"] --> ChatWidget["ChatWidget"]
```
**Sources:** [src/vs/workbench/contrib/chat/common/chatService/chatService.ts:58-66](), [src/vs/workbench/contrib/chat/browser/widget/input/chatInputPart.ts:83-100](), [extensions/copilot/package.json:155-187]()

### Component Relationship Matrix

| Component | Role | Primary Code Entry Point |
| :--- | :--- | :--- |
| **Chat Widget** | Main UI Container | `ChatWidget` [src/vs/workbench/contrib/chat/browser/chat.ts:69-69]() |
| **Chat Service** | Lifecycle & Streaming | `IChatService` [src/vs/workbench/contrib/chat/common/chatService/chatService.ts:59-59]() |
| **Chat Model** | State Management | `ChatModel` [src/vs/workbench/contrib/chat/common/model/chatModel.ts:57-57]() |
| **Agent Service** | Agent Registry | `IChatAgentService` [src/vs/workbench/contrib/chat/common/participants/chatAgents.ts:53-53]() |
| **Session Service** | Provider Registry | `IChatSessionsService` [src/vs/workbench/contrib/chat/common/chatSessionsService.ts:74-74]() |
| **Chat Renderer** | UI Element Rendering | `ChatListRenderer` [src/vs/workbench/contrib/chat/browser/widget/chatListRenderer.ts:13-14]() |

### Session Management
AI interactions are grouped into sessions. The `IChatSessionsService` tracks available session providers and their capabilities [src/vs/workbench/contrib/chat/common/chatSessionsService.ts:74-74](). Providers can be local or remote, such as the `AgentSessionProviders.Local` [src/vs/workbench/contrib/chat/browser/agentSessions/agentSessions.ts:37-37]().

**Session and Provider Registry**
```mermaid
classDiagram
    class IChatWidgetService {
        +lastFocusedWidget: IChatWidget
    }
    class IChatService {
        +getSession(uri): IChatModel
    }
    class IChatSessionsService {
        +getSessions(type): IChatSessionItem[]
    }
    class ChatModel {
        +sessionId: string
        +editingSession: IChatEditingSession
    }
    class IChatAgentService {
        +getAgent(id): IChatAgentData
    }

    ["IChatWidgetService"] --> ["IChatService"] : queries
    ["IChatService"] --> ["ChatModel"] : manages
    ["IChatSessionsService"] --> ["IChatService"] : interacts
    ["ChatModel"] --> ["IChatAgentService"] : invokes
```
**Sources:** [src/vs/workbench/contrib/chat/common/chatSessionsService.ts:74-74](), [src/vs/workbench/contrib/chat/common/chatService/chatService.ts:58-59](), [src/vs/workbench/contrib/chat/browser/actions/chatExecuteActions.ts:35-37]()

### Configuration
Copilot and AI features are governed by settings prefixed with `github.copilot` and `chat.` [extensions/copilot/src/platform/configuration/common/configurationService.ts:28-28](). Key settings include:
*   `github.copilot.chat.executionSubagent.enabled`: Toggles subagent participation [extensions/copilot/package.json:188-188]().
*   `chat.editing.confirmEditRequestRemoval`: Controls safety prompts during undo [src/vs/workbench/contrib/chat/browser/actions/chatExecuteActions.ts:91-91]().
*   `github.copilot.chat.semanticSearchTool.mode`: Determines how codebase search is used [extensions/copilot/package.json:163-163]().

**Sources:** [extensions/copilot/src/platform/configuration/common/configurationService.ts:28-30](), [src/vs/workbench/contrib/chat/browser/actions/chatExecuteActions.ts:90-117](), [extensions/copilot/package.json:163-188]()