import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

export default function ChatWithImagePrompt() {
  const [images, setImages] = useState([]);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    const imagePreviews = acceptedFiles.map((file) =>
      Object.assign(file, {
        preview: URL.createObjectURL(file),
      })
    );
    setImages((prev) => [...prev, ...imagePreviews]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [] },
    multiple: true,
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResponse(null);

    const formData = new FormData();
    images.forEach((file) => {
      formData.append("images", file);
    });
    formData.append("message", prompt);
    formData.append("context", "");

    try {
      const res = await fetch("http://localhost:8000/ask", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      setResponse(data);
    } catch (err) {
      console.error("Error:", err);
      alert("Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center p-6">
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-xl p-6 space-y-4">
        <h1 className="text-2xl font-bold">Chat + Image Prompt</h1>

        <div
          {...getRootProps()}
          className="border-2 border-dashed border-gray-300 rounded-xl p-6 text-center hover:border-gray-500 cursor-pointer transition"
        >
          <input {...getInputProps()} />
          {isDragActive ? (
            <p>Drop images here...</p>
          ) : (
            <p>Drag & drop multiple images here, or click to select</p>
          )}
        </div>

        {images.length > 0 && (
          <div className="grid grid-cols-4 gap-2">
            {images.map((file, index) => (
              <div key={index} className="relative">
                <img
                  src={file.preview}
                  alt={`img-${index}`}
                  className="w-full h-24 object-cover rounded-lg"
                />
                <span className="absolute top-1 left-1 bg-black text-white text-xs px-1 rounded">
                  {index + 1}
                </span>
              </div>
            ))}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3">
          <textarea
            className="w-full border border-gray-300 rounded-xl p-3 resize-none"
            rows="3"
            placeholder="Type your prompt here, e.g., combine image 1 with image 2"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />
          <button
            type="submit"
            className="bg-black text-white px-5 py-2 rounded-xl hover:bg-gray-800 transition"
            disabled={loading}
          >
            {loading ? "Processing..." : "Submit"}
          </button>
        </form>

        {response && (
          <div className="mt-4 border-t pt-4">
            <h2 className="font-semibold">Response:</h2>
            <p><strong>Category:</strong> {response.category}</p>
            <p>{response.response}</p>
          </div>
        )}
      </div>
    </div>
  );
}
