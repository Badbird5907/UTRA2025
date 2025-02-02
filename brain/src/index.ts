import { createClient } from "redis";
import fs from "fs";
import { ollama } from "ollama-ai-provider";
import { CoreMessage, generateText } from "ai";
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

const elevenlabs = new ElevenLabsClient({
  apiKey: process.env.ELEVENLABS_API_KEY,
});

const redis = createClient({
  url: process.env.REDIS_URL,
});

redis.connect();

const PROMPT = fs.readFileSync("prompts/system.txt", "utf8");
const chat = ollama("llama3.2:1b", {})
const messages: CoreMessage[] = []
const publisher = redis.duplicate();
await publisher.connect();


redis.subscribe("ai:trigger", (message: string) => {
  console.log(message);
  const { age, gender, mood, text } = JSON.parse(message); // { "age": 20, "gender": "male", "mood": "happy" }
  const textStr = text ? `: ${text}` : "";
  messages.push({
    role: "user",
    content: `Age: ${age}, Gender: ${gender}, Mood: ${mood}${textStr}`
  })

  console.log("Prompting", messages)
  generateText({
    model: chat,
    maxTokens: 1024,
    messages,
    system: PROMPT
  }).then(async (result) => {
    console.log(result.text)
    messages.push({
      role: "assistant",
      content: result.text
    })
    const promises = []

    const audioStream = await elevenlabs.textToSpeech.convertAsStream("cgSgspJ2msm6clMCkdW9", {
      text: result.text,
      model_id: "eleven_flash_v2_5",
    })
    
    // Create ffplay process to play the audio
    const ffplay = spawn('ffplay', [
      '-i', 'pipe:0',  // Read from stdin
      '-autoexit',     // Exit when the file is done playing
      //'-nodisp'        // Don't display video window
    ]);

    // Pipe the audio stream to ffplay
    Readable.from(audioStream).pipe(ffplay.stdin);

    promises.push(new Promise((resolve) => {
      ffplay.on('close', resolve);
    }));
    
    promises.push(publisher.publish("ai:response", JSON.stringify({
      text: result.text,
      messages
    })));

    await Promise.all(promises);
  })
});




