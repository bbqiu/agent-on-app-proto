import { z } from "zod";

// Zod schemas for runtime validation
export const ResponseAnnotationSchema = z.object({
  type: z.enum(["file_citation", "url_citation", "container_file_citation"]),
  text: z.string(),
  start_index: z.number(),
  end_index: z.number(),
  url: z.string().optional(),
  file_id: z.string().optional(),
  container_file_id: z.string().optional(),
});

export const ResponseOutputTextSchema = z.object({
  type: z.literal("output_text"),
  text: z.string(),
  annotations: z.array(ResponseAnnotationSchema).optional(),
});

export const ResponseOutputMessageSchema = z.object({
  type: z.literal("message"),
  id: z.string(),
  role: z.literal("assistant"),
  content: z.array(ResponseOutputTextSchema),
});

export const ResponseToolCallSchema = z.object({
  type: z.literal("function_call"),
  id: z.string(),
  call_id: z.string(),
  name: z.string(),
  arguments: z.string(),
  status: z.enum(["pending", "completed", "failed"]).optional(),
});

export const ResponseToolCallOutputSchema = z.object({
  type: z.literal("function_call_output"),
  call_id: z.string(),
  output: z.string(),
});

export const ResponseReasoningItemSchema = z.object({
  type: z.literal("reasoning"),
  id: z.string(),
  summary: z.string(),
  content: z.string().optional(),
});

export const ResponseErrorSchema = z.object({
  code: z.string(),
  message: z.string(),
});

export const ResponseErrorItemSchema = z.object({
  type: z.literal("error"),
  code: z.string(),
  message: z.string(),
});

export const ResponseOutputItemSchema = z.discriminatedUnion("type", [
  ResponseOutputMessageSchema,
  ResponseToolCallSchema,
  ResponseToolCallOutputSchema,
  ResponseReasoningItemSchema,
  ResponseErrorItemSchema,
]);

export const ResponseInputMessageSchema = z.object({
  type: z.literal("message"),
  role: z.enum(["user", "developer", "system"]),
  content: z.string(),
});

export const ResponseInputItemSchema = z.discriminatedUnion("type", [
  ResponseInputMessageSchema,
  ResponseOutputItemSchema,
]);

export const ResponseOutputItemDoneSchema = z.object({
  type: z.literal("response.output_item.done"),
  item: ResponseOutputItemSchema,
});

export const ResponseOutputTextDeltaSchema = z.object({
  type: z.literal("response.output_text.delta"),
  delta: z.string(),
  item_id: z.string(),
  output_index: z.number().optional(),
  sequence_number: z.number().optional(),
  content_index: z.number().optional(),
});

export const ResponseOutputTextAnnotationAddedEventSchema = z.object({
  annotation: ResponseAnnotationSchema,
  annotation_index: z.number(),
  content_index: z.number(),
  item_id: z.string(),
  output_index: z.number(),
  sequence_number: z.number(),
  type: z.literal("response.output_text.annotation.added"),
});

/////////////////////////////////////////////////
/////////////// aggregate types /////////////////
/////////////////////////////////////////////////

export const ResponsesResponseSchema = z.object({
  id: z.string(),
  output: z.array(ResponseOutputItemSchema),
  error: ResponseErrorSchema.optional(),
});

export const ResponsesStreamEventSchema = z.discriminatedUnion("type", [
  ResponseOutputItemDoneSchema,
  ResponseOutputTextDeltaSchema,
  ResponseErrorItemSchema,
  ResponseOutputTextAnnotationAddedEventSchema,
]);

export const ResponsesAgentRequestSchema = z.object({
  input: z.array(ResponseInputItemSchema),
  stream: z.boolean().optional(),
  databricks_options: z
    .object({
      return_trace: z.boolean().optional(),
    })
    .optional(),
});


export const ChatStateSchema = z.object({
  input: z.array(ResponseInputItemSchema),
  isLoading: z.boolean(),
  error: z.string().optional(),
});

// Type inference from Zod schemas
export type ResponseAnnotation = z.infer<typeof ResponseAnnotationSchema>;
export type ResponseOutputText = z.infer<typeof ResponseOutputTextSchema>;
export type ResponseOutputMessage = z.infer<typeof ResponseOutputMessageSchema>;
export type ResponseToolCall = z.infer<typeof ResponseToolCallSchema>;
export type ResponseToolCallOutput = z.infer<
  typeof ResponseToolCallOutputSchema
>;
export type ResponseReasoningItem = z.infer<typeof ResponseReasoningItemSchema>;
export type ResponseError = z.infer<typeof ResponseErrorSchema>;
export type ResponseErrorItem = z.infer<typeof ResponseErrorItemSchema>;
export type ResponseOutputItem = z.infer<typeof ResponseOutputItemSchema>;
export type ResponseInputMessage = z.infer<typeof ResponseInputMessageSchema>;
export type ResponseInputItem = z.infer<typeof ResponseInputItemSchema>;
export type ResponsesResponse = z.infer<typeof ResponsesResponseSchema>;
export type ResponseOutputItemDone = z.infer<
  typeof ResponseOutputItemDoneSchema
>;
export type ResponseTextDeltaEvent = z.infer<
  typeof ResponseOutputTextDeltaSchema
>;
export type ResponseOutputTextAnnotationAddedEvent = z.infer<
  typeof ResponseOutputTextAnnotationAddedEventSchema
>;
export type ResponsesStreamEvent = z.infer<typeof ResponsesStreamEventSchema>;
export type ResponsesAgentRequest = z.infer<typeof ResponsesAgentRequestSchema>;
export type ChatState = z.infer<typeof ChatStateSchema>;
