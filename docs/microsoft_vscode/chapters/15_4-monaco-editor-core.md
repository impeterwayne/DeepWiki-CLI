---
title: "Monaco Editor Core"
chapter: 15
source_url: "https://deepwiki.com/microsoft/vscode/4-monaco-editor-core"
word_count: 842
mermaid_diagrams: 2
---

# Monaco Editor Core

<details>
<summary>Relevant source files</summary>

The following files were used as context for generating this wiki page:

- [extensions/css-language-features/server/test/linksTestFixtures/node_modules/foo/package.json](extensions/css-language-features/server/test/linksTestFixtures/node_modules/foo/package.json)
- [extensions/ipynb/src/notebookImagePaste.ts](extensions/ipynb/src/notebookImagePaste.ts)
- [extensions/vscode-api-tests/package.json](extensions/vscode-api-tests/package.json)
- [extensions/vscode-api-tests/src/singlefolder-tests/chat.test.ts](extensions/vscode-api-tests/src/singlefolder-tests/chat.test.ts)
- [extensions/vscode-colorize-tests/src/colorizer.test.ts](extensions/vscode-colorize-tests/src/colorizer.test.ts)
- [src/vs/base/common/arrays.ts](src/vs/base/common/arrays.ts)
- [src/vs/base/test/common/arrays.test.ts](src/vs/base/test/common/arrays.test.ts)
- [src/vs/editor/browser/controller/editContext/clipboardUtils.ts](src/vs/editor/browser/controller/editContext/clipboardUtils.ts)
- [src/vs/editor/browser/controller/editContext/editContext.ts](src/vs/editor/browser/controller/editContext/editContext.ts)
- [src/vs/editor/browser/controller/editContext/native/debugEditContext.ts](src/vs/editor/browser/controller/editContext/native/debugEditContext.ts)
- [src/vs/editor/browser/controller/editContext/native/editContextFactory.ts](src/vs/editor/browser/controller/editContext/native/editContextFactory.ts)
- [src/vs/editor/browser/controller/editContext/native/nativeEditContext.css](src/vs/editor/browser/controller/editContext/native/nativeEditContext.css)
- [src/vs/editor/browser/controller/editContext/native/nativeEditContext.ts](src/vs/editor/browser/controller/editContext/native/nativeEditContext.ts)
- [src/vs/editor/browser/controller/editContext/native/nativeEditContextUtils.ts](src/vs/editor/browser/controller/editContext/native/nativeEditContextUtils.ts)
- [src/vs/editor/browser/controller/editContext/native/screenReaderContentRich.ts](src/vs/editor/browser/controller/editContext/native/screenReaderContentRich.ts)
- [src/vs/editor/browser/controller/editContext/native/screenReaderContentSimple.ts](src/vs/editor/browser/controller/editContext/native/screenReaderContentSimple.ts)
- [src/vs/editor/browser/controller/editContext/native/screenReaderSupport.ts](src/vs/editor/browser/controller/editContext/native/screenReaderSupport.ts)
- [src/vs/editor/browser/controller/editContext/native/screenReaderUtils.ts](src/vs/editor/browser/controller/editContext/native/screenReaderUtils.ts)
- [src/vs/editor/browser/controller/editContext/screenReaderUtils.ts](src/vs/editor/browser/controller/editContext/screenReaderUtils.ts)
- [src/vs/editor/browser/controller/editContext/textArea/textAreaEditContext.ts](src/vs/editor/browser/controller/editContext/textArea/textAreaEditContext.ts)
- [src/vs/editor/browser/controller/editContext/textArea/textAreaEditContextInput.ts](src/vs/editor/browser/controller/editContext/textArea/textAreaEditContextInput.ts)
- [src/vs/editor/browser/controller/editContext/textArea/textAreaEditContextState.ts](src/vs/editor/browser/controller/editContext/textArea/textAreaEditContextState.ts)
- [src/vs/editor/browser/controller/mouseHandler.ts](src/vs/editor/browser/controller/mouseHandler.ts)
- [src/vs/editor/browser/controller/mouseTarget.ts](src/vs/editor/browser/controller/mouseTarget.ts)
- [src/vs/editor/browser/controller/pointerHandler.ts](src/vs/editor/browser/controller/pointerHandler.ts)
- [src/vs/editor/browser/editorBrowser.ts](src/vs/editor/browser/editorBrowser.ts)
- [src/vs/editor/browser/editorDom.ts](src/vs/editor/browser/editorDom.ts)
- [src/vs/editor/browser/view.ts](src/vs/editor/browser/view.ts)
- [src/vs/editor/browser/view/viewController.ts](src/vs/editor/browser/view/viewController.ts)
- [src/vs/editor/browser/view/viewUserInputEvents.ts](src/vs/editor/browser/view/viewUserInputEvents.ts)
- [src/vs/editor/browser/widget/codeEditor/codeEditorWidget.ts](src/vs/editor/browser/widget/codeEditor/codeEditorWidget.ts)
- [src/vs/editor/common/config/editorConfigurationSchema.ts](src/vs/editor/common/config/editorConfigurationSchema.ts)
- [src/vs/editor/common/config/editorOptions.ts](src/vs/editor/common/config/editorOptions.ts)
- [src/vs/editor/common/editorCommon.ts](src/vs/editor/common/editorCommon.ts)
- [src/vs/editor/common/languages.ts](src/vs/editor/common/languages.ts)
- [src/vs/editor/common/model.ts](src/vs/editor/common/model.ts)
- [src/vs/editor/common/model/textModel.ts](src/vs/editor/common/model/textModel.ts)
- [src/vs/editor/common/standalone/standaloneEnums.ts](src/vs/editor/common/standalone/standaloneEnums.ts)
- [src/vs/editor/common/viewModel/screenReaderSimpleModel.ts](src/vs/editor/common/viewModel/screenReaderSimpleModel.ts)
- [src/vs/editor/common/viewModel/viewModelImpl.ts](src/vs/editor/common/viewModel/viewModelImpl.ts)
- [src/vs/editor/contrib/clipboard/browser/clipboard.ts](src/vs/editor/contrib/clipboard/browser/clipboard.ts)
- [src/vs/editor/contrib/dropOrPasteInto/browser/copyPasteContribution.ts](src/vs/editor/contrib/dropOrPasteInto/browser/copyPasteContribution.ts)
- [src/vs/editor/contrib/dropOrPasteInto/browser/copyPasteController.ts](src/vs/editor/contrib/dropOrPasteInto/browser/copyPasteController.ts)
- [src/vs/editor/contrib/dropOrPasteInto/browser/defaultProviders.ts](src/vs/editor/contrib/dropOrPasteInto/browser/defaultProviders.ts)
- [src/vs/editor/contrib/dropOrPasteInto/browser/dropIntoEditorContribution.ts](src/vs/editor/contrib/dropOrPasteInto/browser/dropIntoEditorContribution.ts)
- [src/vs/editor/contrib/dropOrPasteInto/browser/dropIntoEditorController.ts](src/vs/editor/contrib/dropOrPasteInto/browser/dropIntoEditorController.ts)
- [src/vs/editor/contrib/dropOrPasteInto/browser/edit.ts](src/vs/editor/contrib/dropOrPasteInto/browser/edit.ts)
- [src/vs/editor/contrib/dropOrPasteInto/browser/postEditWidget.css](src/vs/editor/contrib/dropOrPasteInto/browser/postEditWidget.css)
- [src/vs/editor/contrib/dropOrPasteInto/browser/postEditWidget.ts](src/vs/editor/contrib/dropOrPasteInto/browser/postEditWidget.ts)
- [src/vs/editor/contrib/dropOrPasteInto/test/browser/editSort.test.ts](src/vs/editor/contrib/dropOrPasteInto/test/browser/editSort.test.ts)
- [src/vs/editor/contrib/inlayHints/browser/inlayHintsController.ts](src/vs/editor/contrib/inlayHints/browser/inlayHintsController.ts)
- [src/vs/editor/contrib/inlineCompletions/browser/controller/commandIds.ts](src/vs/editor/contrib/inlineCompletions/browser/controller/commandIds.ts)
- [src/vs/editor/contrib/inlineCompletions/browser/controller/commands.ts](src/vs/editor/contrib/inlineCompletions/browser/controller/commands.ts)
- [src/vs/editor/contrib/inlineCompletions/browser/controller/inlineCompletionContextKeys.ts](src/vs/editor/contrib/inlineCompletions/browser/controller/inlineCompletionContextKeys.ts)
- [src/vs/editor/contrib/inlineCompletions/browser/controller/inlineCompletionsController.ts](src/vs/editor/contrib/inlineCompletions/browser/controller/inlineCompletionsController.ts)
- [src/vs/editor/contrib/inlineCompletions/browser/inlineCompletions.contribution.ts](src/vs/editor/contrib/inlineCompletions/browser/inlineCompletions.contribution.ts)
- [src/vs/editor/contrib/inlineCompletions/browser/model/inlineCompletionsModel.ts](src/vs/editor/contrib/inlineCompletions/browser/model/inlineCompletionsModel.ts)
- [src/vs/editor/contrib/inlineCompletions/browser/model/inlineCompletionsSource.ts](src/vs/editor/contrib/inlineCompletions/browser/model/inlineCompletionsSource.ts)
- [src/vs/editor/contrib/inlineCompletions/browser/model/inlineSuggestionItem.ts](src/vs/editor/contrib/inlineCompletions/browser/model/inlineSuggestionItem.ts)
- [src/vs/editor/contrib/inlineCompletions/browser/model/provideInlineCompletions.ts](src/vs/editor/contrib/inlineCompletions/browser/model/provideInlineCompletions.ts)
- [src/vs/editor/contrib/inlineCompletions/browser/telemetry.ts](src/vs/editor/contrib/inlineCompletions/browser/telemetry.ts)
- [src/vs/editor/contrib/inlineCompletions/browser/view/inlineEdits/inlineEditWithChanges.ts](src/vs/editor/contrib/inlineCompletions/browser/view/inlineEdits/inlineEditWithChanges.ts)
- [src/vs/editor/contrib/inlineCompletions/browser/view/inlineEdits/inlineEditsModel.ts](src/vs/editor/contrib/inlineCompletions/browser/view/inlineEdits/inlineEditsModel.ts)
- [src/vs/editor/contrib/inlineCompletions/browser/view/inlineEdits/inlineEditsView.ts](src/vs/editor/contrib/inlineCompletions/browser/view/inlineEdits/inlineEditsView.ts)
- [src/vs/editor/contrib/inlineCompletions/browser/view/inlineEdits/inlineEditsViewInterface.ts](src/vs/editor/contrib/inlineCompletions/browser/view/inlineEdits/inlineEditsViewInterface.ts)
- [src/vs/editor/contrib/inlineCompletions/browser/view/inlineEdits/inlineEditsViewProducer.ts](src/vs/editor/contrib/inlineCompletions/browser/view/inlineEdits/inlineEditsViewProducer.ts)
- [src/vs/editor/test/browser/controller/imeRecordedTypes.ts](src/vs/editor/test/browser/controller/imeRecordedTypes.ts)
- [src/vs/editor/test/browser/controller/nativeEditContextUtils.test.ts](src/vs/editor/test/browser/controller/nativeEditContextUtils.test.ts)
- [src/vs/editor/test/browser/controller/textAreaInput.test.ts](src/vs/editor/test/browser/controller/textAreaInput.test.ts)
- [src/vs/editor/test/browser/controller/textAreaState.test.ts](src/vs/editor/test/browser/controller/textAreaState.test.ts)
- [src/vs/editor/test/browser/view/viewController.test.ts](src/vs/editor/test/browser/view/viewController.test.ts)
- [src/vs/monaco.d.ts](src/vs/monaco.d.ts)
- [src/vs/platform/extensions/common/extensionsApiProposals.ts](src/vs/platform/extensions/common/extensionsApiProposals.ts)
- [src/vs/workbench/api/browser/mainThreadChatAgents2.ts](src/vs/workbench/api/browser/mainThreadChatAgents2.ts)
- [src/vs/workbench/api/browser/mainThreadLanguageFeatures.ts](src/vs/workbench/api/browser/mainThreadLanguageFeatures.ts)
- [src/vs/workbench/api/common/extHost.api.impl.ts](src/vs/workbench/api/common/extHost.api.impl.ts)
- [src/vs/workbench/api/common/extHost.protocol.ts](src/vs/workbench/api/common/extHost.protocol.ts)
- [src/vs/workbench/api/common/extHostChatAgents2.ts](src/vs/workbench/api/common/extHostChatAgents2.ts)
- [src/vs/workbench/api/common/extHostLanguageFeatures.ts](src/vs/workbench/api/common/extHostLanguageFeatures.ts)
- [src/vs/workbench/api/common/extHostTypeConverters.ts](src/vs/workbench/api/common/extHostTypeConverters.ts)
- [src/vs/workbench/api/common/extHostTypes.ts](src/vs/workbench/api/common/extHostTypes.ts)
- [src/vs/workbench/contrib/dropOrPasteInto/browser/commands.ts](src/vs/workbench/contrib/dropOrPasteInto/browser/commands.ts)
- [src/vs/workbench/contrib/dropOrPasteInto/browser/dropOrPasteInto.contribution.ts](src/vs/workbench/contrib/dropOrPasteInto/browser/dropOrPasteInto.contribution.ts)
- [src/vscode-dts/vscode.d.ts](src/vscode-dts/vscode.d.ts)
- [src/vscode-dts/vscode.proposed.chatParticipantAdditions.d.ts](src/vscode-dts/vscode.proposed.chatParticipantAdditions.d.ts)
- [src/vscode-dts/vscode.proposed.inlineCompletionsAdditions.d.ts](src/vscode-dts/vscode.proposed.inlineCompletionsAdditions.d.ts)

</details>



The Monaco Editor is the core text editing component of VS Code. It is responsible for the efficient representation of text documents, the management of visual state (word wrap, folding, projections), and the orchestration of complex language features and user interface elements within the editor viewport.

The editor is built on a strict Model-View-ViewModel (MVVM) architecture to separate heavy-duty text manipulation from DOM-heavy rendering logic.

### Core Architecture Overview

The editor's lifecycle and data flow are managed through three primary layers:
1.  **TextModel**: The "Source of Truth." It handles raw text via a `PieceTreeTextBuffer`, manages edit operations, and the undo/redo stack [src/vs/editor/common/model/textModel.ts:46-56]().
2.  **ViewModel**: The "Visual Logic." It translates the flat text model into a visual representation, handling line projections (like word wrap) and coordinating decorations [src/vs/editor/common/viewModel/viewModelImpl.ts:51-125]().
3.  **View**: The "Renderer." It interacts with the DOM to display lines, cursors, and widgets [src/vs/editor/browser/view.ts:32-60]().

The following diagram illustrates the relationship between these core entities:

#### Editor Data Flow
```mermaid
graph TD
    subgraph Model_Layer ["Model Layer"]
        TM["TextModel (vs/editor/common/model/textModel.ts)"]
        ES["EditStack (vs/editor/common/model/textModel.ts)"]
    end

    subgraph ViewModel_Layer ["ViewModel Layer"]
        VM["ViewModel (vs/editor/common/viewModel/viewModelImpl.ts)"]
        CC["CursorsController (vs/editor/common/cursor/cursor.ts)"]
    end

    subgraph View_Layer ["View Layer"]
        V["View (vs/editor/browser/view.ts)"]
        CW["ViewContentWidgets (vs/editor/browser/viewParts/contentWidgets/contentWidgets.ts)"]
    end

    TM -- "IModelContentChangedEvent" --> VM
    VM -- "ViewEvents" --> V
    V -- "ViewController" --> VM
    VM -- "CursorsController" --> TM
    TM -- "pushEditOperation" --> ES
```
**Sources:** [src/vs/editor/common/model/textModel.ts:40-57](), [src/vs/editor/common/viewModel/viewModelImpl.ts:86-125](), [src/vs/editor/common/model/textModel.ts:46-56]()

---

## 4.1 Text Model and View Model
The `TextModel` manages the buffer of text and maintains document state, including decorations and tokenization state [src/vs/editor/common/model/textModel.ts:40-56](). It provides the underlying data structure for all text-based operations using a `PieceTreeTextBuffer` for efficient large-file handling [src/vs/editor/common/model/textModel.ts:50-51](). The `UndoRedoService` tracks changes across resources to provide robust undo/redo capabilities [src/vs/editor/common/model/textModel.ts:23-23]().

The `ViewModel` acts as a proxy between the model and the view. Its primary responsibility is "Line Projection"—calculating how a model line maps to a view line (e.g., visual lines created by word wrap) [src/vs/editor/common/viewModel/viewModelImpl.ts:98-120](). It also coordinates `ViewModelDecorations` which are visual-only markers filtered from the model [src/vs/editor/common/viewModel/viewModelImpl.ts:66-66]().

For details, see [Text Model and View Model](#4.1).

**Sources:** [src/vs/editor/common/model/textModel.ts:111-121](), [src/vs/editor/common/viewModel/viewModelImpl.ts:51-125](), [src/vs/editor/common/model/textModel.ts:46-56]()

---

## 4.2 Editor Rendering and Input Handling
The rendering pipeline is highly optimized to minimize DOM churn, rendering only the visible lines in the viewport. Input is handled via a specialized `EditContext`. The editor supports various strategies for rendering, including experimental GPU acceleration and sophisticated whitespace rendering [src/vs/editor/common/config/editorOptions.ts:223-224]().

Input handling is managed by specialized contexts such as `NativeEditContext` for modern browser APIs [src/vs/editor/browser/controller/editContext/native/nativeEditContext.ts:27-50]() or `TextAreaEditContext` for legacy compatibility [src/vs/editor/browser/controller/editContext/textArea/textAreaEditContext.ts:24-40](). The editor also manages `ContentWidgetPositionPreference` for elements like the suggest widget that float over the text [src/vs/editor/common/standalone/standaloneEnums.ts:84-97]().

For details, see [Editor Rendering and Input Handling](#4.2).

**Sources:** [src/vs/editor/common/config/editorOptions.ts:223-224](), [src/vs/editor/common/standalone/standaloneEnums.ts:84-97](), [src/vs/editor/browser/controller/editContext/native/nativeEditContext.ts:27-50]()

---

## 4.3 Language Features and Editor Contributions
The Monaco Editor provides a rich set of language features through a provider-based architecture defined in `languages.ts` [src/vs/editor/common/languages.ts:1-223](). This includes IntelliSense (completions, hovers) and Navigation (definitions). Features are registered with the `ILanguageFeaturesService` [src/vs/workbench/api/browser/mainThreadLanguageFeatures.ts:55-55]().

These features are often implemented as editor contribution classes. For example, the `MainThreadLanguageFeatures` coordinates communication between the renderer and the extension host for features like diagnostics and word definitions [src/vs/workbench/api/browser/mainThreadLanguageFeatures.ts:65-90]().

#### Language Feature and Contribution Architecture
```mermaid
graph LR
    subgraph Language_Services ["Language Services"]
        LFS["ILanguageFeaturesService (vs/editor/common/services/languageFeatures.ts)"]
        HP["HoverProvider (vs/editor/common/languages.ts)"]
    end

    subgraph Extension_Host_Boundary ["Extension Host Boundary"]
        MTLF["MainThreadLanguageFeatures (vs/workbench/api/browser/mainThreadLanguageFeatures.ts)"]
        EHLF["ExtHostLanguageFeatures (vs/workbench/api/common/extHostLanguageFeatures.ts)"]
    end

    MTLF -- "RPC Protocol" --> EHLF
    EHLF -- "Invokes Extension" --> HP
    MTLF -- "Registers with" --> LFS
```
**Sources:** [src/vs/workbench/api/browser/mainThreadLanguageFeatures.ts:46-98](), [src/vs/workbench/api/common/extHostLanguageFeatures.ts:43-105](), [src/vs/editor/common/languages.ts:217-223]()

For details, see [Language Features and Editor Contributions](#4.3).

---

## 4.4 Inline Completions and Ghost Text
The `InlineCompletionsModel` manages the state for "Ghost Text" (unaccepted suggestions appearing inline) [src/vs/editor/contrib/inlineCompletions/browser/model/inlineCompletionsModel.ts:59-110](). This system uses observables to track changes and update the visual state of completions [src/vs/editor/contrib/inlineCompletions/browser/model/inlineCompletionsModel.ts:11-13](). 

It supports sophisticated "Inline Edits" rendered via `InlineEditsView`, which can show side-by-side diffs, insertions, or deletions directly within the editor flow [src/vs/editor/contrib/inlineCompletions/browser/view/inlineEdits/inlineEditsView.ts:86-125](). Suggestions are fetched via the `InlineCompletionsSource` which interacts with registered `InlineCompletionsProvider` instances and manages the request lifecycle [src/vs/editor/contrib/inlineCompletions/browser/model/inlineCompletionsSource.ts:42-100]().

For details, see [Inline Completions and Ghost Text](#4.4).

**Sources:** [src/vs/editor/contrib/inlineCompletions/browser/model/inlineCompletionsModel.ts:59-110](), [src/vs/editor/contrib/inlineCompletions/browser/view/inlineEdits/inlineEditsView.ts:86-125](), [src/vs/editor/contrib/inlineCompletions/browser/model/inlineCompletionsSource.ts:42-100]()26