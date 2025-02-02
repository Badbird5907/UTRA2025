import { createClient } from "redis";
import fs from "fs";
import { ollama } from "ollama-ai-provider";
import { CoreMessage, generateText, streamText } from "ai";
import { ElevenLabsClient, stream } from "elevenlabs";
import { Readable } from "stream";
import { spawn } from 'child_process';

console.log("Hello World!");

if (!process.env.REDIS_URL) {
  throw new Error("REDIS_URL is not set");
}
if (!process.env.ELEVENLABS_API_KEY) {
  throw new Error("ELEVENLABS_API_KEY is not set");
}

const redis = createClient({
  url: process.env.REDIS_URL,
});

const PROMPT = fs.readFileSync("prompts/system.txt", "utf8");
const chat = ollama("llama3.2:1b", {})
const messages: CoreMessage[] = []
const publisher = redis.duplicate();
const kv = redis.duplicate();
await Promise.all([
  publisher.connect(),
  kv.connect(),
  redis.connect(),
]);


redis.subscribe("ai:trigger", async (message: string) => {
  kv.set("ai:lock", "true");
  console.log(message);
  
  messages.push({
    role: "user",
    content: `${redis.get("face_data")} ${message}`
  })

  console.log("Prompting", messages)
  const { textStream } = streamText({
    model: chat,
    maxTokens: 1024,
    messages,
    system: PROMPT
  })

  const voiceId = "cgSgspJ2msm6clMCkdW9";
  const model = "eleven_flash_v2_5";
  const wsUrl = `wss://api.elevenlabs.io/v1/text-to-speech/${voiceId}/stream-input?model_id=${model}`;
  const socket = new WebSocket(wsUrl);

  // init ws conn
  await new Promise((resolve) => {
    socket.onopen = () => {
      socket.send(JSON.stringify({
        text: " ",
        voice_settings: {
          stability: 0.5,
          similarity_boost: 0.8
        },
        xi_api_key: process.env.ELEVENLABS_API_KEY
      }));
      resolve(null);
    };
  });

  // init ffplay process
  let ffplay;

  try {
    ffplay = spawn('ffplay', [
      '-i', 'pipe:0',
      '-autoexit'
    ]);

    ffplay.on('error', (err) => {
      console.error('Failed to start ffplay. Make sure FFmpeg is installed.');
      socket.close();
    });
  } catch (error) {
    console.error('Failed to initialize ffplay:', error);
    socket.close();
    return;
  }

  // handle ws messages
  socket.onmessage = (event) => {
    const response = JSON.parse(event.data);
    const { audio, ...logData } = response;
    console.log("[ELEVENLABS]", logData);
    if (audio && ffplay?.stdin) {

      const audioChunk = Buffer.from(audio, 'base64');
      ffplay.stdin.write(audioChunk);
    } else if (response.isFinal && ffplay?.stdin) {
      ffplay.stdin.end();
    }
  };

  let generatedText = "";
  for await (const chunk of textStream) {
    // process.stdout.write(chunk);
    console.log("[AI]", chunk)
    generatedText += chunk;
    
    // send text chunk to elevenlabs
    socket.send(JSON.stringify({
      text: chunk + " "  // Add space as per docs recommendation
    }));

  }
  // process.stdout.write("\n")

  // send eos message to elevenlabs
  socket.send(JSON.stringify({ text: "" }));


  // Wait for ffplay to finish
  await new Promise((resolve) => {
    ffplay.on('close', resolve);
  });

  // close ws conn
  socket.close();

  // update messages and publish response
  messages.push({
    role: "assistant",
    content: generatedText
  });

  await publisher.publish("ai:response", JSON.stringify({
    text: generatedText,
    messages
  }));
  kv.del("ai:lock");
});
