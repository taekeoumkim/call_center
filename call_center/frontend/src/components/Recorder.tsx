// src/components/Recorder.tsx
import { useState, useRef } from 'react';

interface RecorderProps {
  onRecorded: (blob: Blob) => void;
}

export default function Recorder({ onRecorded }: RecorderProps) {
  const [recording, setRecording] = useState(false);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);

  const toggleRecording = async () => {
    if (!recording) {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream);
      audioChunks.current = [];

      mediaRecorder.current.ondataavailable = (e) => {
        audioChunks.current.push(e.data);
      };

      mediaRecorder.current.onstop = () => {
        const blob = new Blob(audioChunks.current, { type: 'audio/webm' });
        onRecorded(blob);
      };

      mediaRecorder.current.start();
      setRecording(true);
    } else {
      mediaRecorder.current?.stop();
      setRecording(false);
    }
  };

  return (
    <div>
      <button
        onClick={toggleRecording}
        className={`p-4 rounded-full text-white ${
          recording ? 'bg-red-600' : 'bg-green-600'
        }`}
      >
        🎙️ {recording ? '녹음 중지' : '녹음 시작'}
      </button>
    </div>
  );
}
