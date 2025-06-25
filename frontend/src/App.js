import React, { useCallback, useEffect, useState } from "react";
import { useDropzone } from "react-dropzone";

export default function ChatWithImagePrompt() {
  const [images, setImages] = useState([]);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  const onDrop = useCallback(
    (acceptedFiles) => {
      // Revoke previews of old images
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);

    if (!prompt.trim()) {
      setError("Please enter a prompt.");
      setLoading(false);
      return;
    }

    const formData = new FormData();
    formData.append("message", prompt);
    formData.append("context", "");

    images.forEach((file) => {
      formData.append("images", file);
    });

    try {
      const res = await fetch("http://localhost:8000/ask", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Server returned error");

      const data = await res.json();
      setResponse(data);
    } catch (err) {
      setError("Something went wrong while processing the request.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Cleanup on component unmount or when images change
  useEffect(() => {
    return () => {
      images.forEach((file) => URL.revokeObjectURL(file.preview));
    };
  }, [images]);

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
            <p>Drag & drop images, or click to upload</p>
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
            placeholder="Type your prompt here..."
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

        {loading && <p className="text-blue-600">Thinking...</p>}
        {error && <p className="text-red-600">{error}</p>}

        {response && (
          <div className="mt-6 border-t pt-6 space-y-3">
            <h2 className="text-xl font-bold text-gray-800">AI Response</h2>

            <div className="bg-gray-50 border-l-4 border-blue-400 p-4 rounded-lg">
              <p className="text-sm text-gray-500 uppercase font-semibold mb-1">
                Category
              </p>
              <p className="text-lg font-medium text-blue-800">{response.category}</p>
            </div>

            <div className="prose max-w-none">
              {response.response
                .split("\n")
                .filter((line) => line.trim() !== "")
                .map((line, idx) => (
                  <p key={idx}>{line}</p>
                ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
