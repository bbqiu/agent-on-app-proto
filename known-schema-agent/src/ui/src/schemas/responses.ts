// OpenAI Response API Types - Ported from universe webapp
// Based on /Users/bryan.qiu/universe/webapp/web/js/genai/shared/responses/types/

export interface ResponsesResponse {
  id: string;
  output: ResponseOutputItem[];
  error?: ResponseErrorItem;
}

export type ResponseOutputItem =
  | ResponseOutputMessage
  | ResponseToolCall
  | ResponseToolCallOutput
  | ResponseReasoningItem
  | ResponseErrorItem;

export interface ResponseOutputMessage {
  type: "message";
  id: string;
  role: "assistant";
  content: ResponseOutputText[];
}

export interface ResponseOutputText {
  type: "text";
  text: string;
  annotations?: ResponseAnnotation[];
}

export interface ResponseAnnotation {
  type: "file_citation" | "url_citation" | "container_file_citation";
  text: string;
  start_index: number;
  end_index: number;
  url?: string;
  file_id?: string;
  container_file_id?: string;
}

export interface ResponseToolCall {
  type: "tool_call";
  id: string;
  function: {
    name: string;
    arguments: string;
  };
  status?: "pending" | "completed" | "failed";
}

export interface ResponseToolCallOutput {
  type: "tool_call_output";
  tool_call_id: string;
  output: string;
  error?: string;
}

export interface ResponseReasoningItem {
  type: "reasoning";
  id: string;
  summary: string;
  content?: string;
}

export interface ResponseErrorItem {
  type: "error";
  code: string;
  message: string;
}

// Streaming Events
// TODO: bbqiu add more types here
export interface ResponsesStreamEvent {
  type: "response.output_item.done";
  item?: ResponseOutputItem;
  error?: ResponseErrorItem;
}

export type ResponseOutputItemDone = {
  type: "response.output_item.done";
  item: ResponseOutputItem;
};

export type ResponseTextDeltaEvent = {
  type: "response.output_text.delta";
  // The text delta that was added.
  delta: string;
  // The ID of the output item that the text delta was added to.
  item_id: string;
  // The index of the output item that the text delta was added to.
  output_index?: number;
  // The sequence number for this event.
  sequence_number?: number;
  // The index of the content part that the text delta was added to.
  content_index?: number;
};

export type ResponseOutputTextAnnotationAddedEvent = {
  // The annotation object being added
  annotation: ResponsesAnnotation;
  // The index of the annotation within the content part.
  annotation_index: number;
  // The index of the content part within the output item.
  content_index: number;
  // The unique identifier of the item to which the annotation is being added.
  item_id: string;
  // The index of the output item in the response's output array.
  output_index: number;
  // The sequence number of this event.
  sequence_number: number;
  // The type of the event. Always 'response.output_text.annotation.added'.
  type: "response.output_text.annotation.added";
};

// Request Types
export interface ResponsesAgentRequest {
  input: ResponseInputItem[];
  stream?: boolean;
  databricks_options?: {
    return_trace?: boolean;
  };
}

export type ResponseInputMessage = {
  type: "message";
  role: "user" | "developer" | "system";
  content: string;
};

export type ResponseInputItem = ResponseInputMessage | ResponseOutputItem;

// Chat UI State
export interface ChatState {
  input: ResponseInputItem[];
  isLoading: boolean;
  error?: string;
}

export interface AgentConfig {
  endpoint: string;
  systemPrompt: string;
}
