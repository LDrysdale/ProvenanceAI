import React, { useCallback, useEffect, useState, useRef } from "react";
import { useDropzone } from "react-dropzone";

export default function ChatWithImagePrompt() {
  const [conversation, setConversation] = useState([]);
  const [prompt, setPrompt] = useState("");
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const scrollRef = useRef(null); // ref to scroll container
  const inputRef = useRef(null);  // ref to textarea input

  const onDrop = useCallback(
    (acceptedFiles) => {
      images.forEach((file) => URL.revokeObjectURL(file.preview));
      const previews = acceptedFiles.map((file) =>
        Object.assign(file, {
          preview: URL.createObjectURL(file),
        })
      );
      setImages(previews);
    },
    [images]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [] },
    multiple: true,
  });

  // Auto scroll to bottom when conversation updates
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [conversation, loading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!prompt.trim()) {
      setError("Please enter a prompt.");
      return;
    }

    setLoading(true);

    const userMessage = {
      id: Date.now() + "-user",
      sender: "user",
      text: prompt,
      images,
    };
    setConversation((prev) => [...prev, userMessage]);
    setPrompt("");
    setImages([]);

    const formData = new FormData();
    formData.append("message", prompt);
    formData.append("context", "");

    userMessage.images.forEach((file) => {
      formData.append("images", file);
    });

    try {
      const res = await fetch("http://localhost:8000/ask", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Server returned error");

      const data = await res.json();

      const aiMessage = {
        id: Date.now() + "-ai",
        sender: "ai",
        text: data.response,
        category: data.category,
      };
      setConversation((prev) => [...prev, aiMessage]);
    } catch (err) {
      setError("Something went wrong while processing the request.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Handle Enter and Shift+Enter in textarea
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!loading) handleSubmit(e);
    }
  };

  useEffect(() => {
    return () => {
      images.forEach((file) => URL.revokeObjectURL(file.preview));
    };
  }, [images]);

  return (
    <div className="min-h-screen bg-[#202123] flex flex-col font-inter">
      <header className="bg-[#343541] py-4 px-6 border-b border-[#444654]">
        <h1 className="text-white text-2xl font-semibold">Chat + Image Prompt</h1>
      </header>

      {/* Conversation area */}
      <main
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-6 py-4 space-y-6 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800"
      >
        {conversation.length === 0 && !loading && (
          <p className="text-gray-400 text-center mt-12">Start by typing your prompt below.</p>
        )}

        {conversation.map((msg) => (
          <div
            key={msg.id}
            className={`flex max-w-3xl ${
              msg.sender === "user" ? "justify-start" : "justify-end"
            }`}
          >
            <div
              className={`rounded-lg px-5 py-3 max-w-[75%] whitespace-pre-wrap ${
                msg.sender === "user"
                  ? "bg-[#444654] text-white rounded-bl-none"
                  : "bg-blue-600 text-white rounded-br-none"
              }`}
            >
              {msg.sender === "user" && msg.images && msg.images.length > 0 && (
                <div className="mb-2 grid grid-cols-4 gap-2">
                  {msg.images.map((file, idx) => (
                    <img
                      key={idx}
                      src={file.preview}
                      alt={`upload-${idx}`}
                      className="w-full h-20 object-cover rounded-md border border-[#555]"
                    />
                  ))}
                </div>
              )}

              <p>{msg.text}</p>

              {msg.sender === "ai" && msg.category && (
                <p className="mt-2 text-xs uppercase font-bold text-blue-300">
                  Category: {msg.category}
                </p>
              )}
            </div>
          </div>
        ))}

        {loading && <p className="text-blue-400 text-center mt-4">Thinking...</p>}
        {error && <p className="text-red-500 text-center mt-4">{error}</p>}
      </main>

      {/* Input area */}
      <footer className="bg-[#343541] p-6 border-t border-[#444654]">
        <form
          onSubmit={handleSubmit}
          className="max-w-3xl mx-auto flex flex-col space-y-3"
          autoComplete="off"
        >
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-4 flex flex-col items-center justify-center cursor-pointer transition-colors
              ${
                isDragActive
                  ? "border-blue-500 bg-[#202123]"
                  : "border-[#444654] hover:border-blue-400 bg-[#202123]"
              }`}
          >
            <input {...getInputProps()} />
            {isDragActive ? (
              <p className="text-blue-400 text-sm">Drop images here...</p>
            ) : (
              <p className="text-gray-400 text-sm">Drag & drop images, or click to upload</p>
            )}
          </div>

          {images.length > 0 && (
            <div className="grid grid-cols-4 gap-3">
              {images.map((file, idx) => (
                <div
                  key={idx}
                  className="relative rounded-md overflow-hidden border border-[#555]"
                >
                  <img
                    src={file.preview}
                    alt={`upload-preview-${idx}`}
                    className="w-full h-20 object-cover"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      setImages((imgs) => imgs.filter((_, i) => i !== idx));
                      URL.revokeObjectURL(file.preview);
                    }}
                    className="absolute top-1 right-1 bg-black bg-opacity-60 rounded-full text-white text-xs w-5 h-5 flex items-center justify-center hover:bg-red-600 transition"
                    aria-label="Remove image"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}

          <textarea
            ref={inputRef}
            rows={3}
            placeholder="Type your prompt here..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full rounded-md border border-[#555] bg-[#202123] text-white px-4 py-3 resize-none placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="self-end bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold px-6 py-2 rounded-md transition"
          >
            {loading ? "Processing..." : "Submit"}
          </button>
        </form>
      </footer>
    </div>
  );
}
