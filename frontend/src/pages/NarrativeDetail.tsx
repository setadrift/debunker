import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import TimelineChart from "../components/TimelineChart";
import type { NarrativeDetail } from "../types";

export default function NarrativeDetail() {
  const { id } = useParams<{ id: string }>();
  const [narrative, setNarrative] = useState<NarrativeDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNarrative = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/narratives/${id}`);
        if (!response.ok) {
          throw new Error("Narrative not found");
        }
        const data = await response.json();
        setNarrative(data);
      } catch (error) {
        console.error("Failed to fetch narrative:", error);
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchNarrative();
    }
  }, [id]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!narrative) {
    return <div>Narrative not found</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">{narrative.summary}</h1>
      <div className="grid grid-cols-3 gap-8">
        <div className="col-span-1">
          <h2 className="text-2xl font-bold mb-4">Timeline</h2>
          <TimelineChart data={narrative.timeline} />
        </div>
        <div className="col-span-2">
          <h2 className="text-2xl font-bold mb-4">Sources</h2>
          <div>
            {narrative.sources.map((source) => (
              <details key={source.id} className="bg-white shadow-md rounded-lg p-4 mb-4">
                <summary className="font-bold cursor-pointer">
                  {source.platform}: {new Date(source.timestamp).toLocaleDateString()}
                </summary>
                <div className="mt-4">
                  <p>{source.text_excerpt}...</p>
                  <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline mt-2 inline-block">
                    View Source
                  </a>
                </div>
              </details>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
} 