import { useEffect, useState } from "react";
import Card from "../components/Card";

type Narrative = {
  id: number;
  summary: string;
  source_count: number;
  last_seen: string;
};

export default function Home() {
  const [narratives, setNarratives] = useState<Narrative[]>([]);

  useEffect(() => {
    const fetchNarratives = async () => {
      const response = await fetch("http://localhost:8000/api/narratives");
      const data = await response.json();
      setNarratives(data);
    };

    fetchNarratives();
  }, []);

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">Top Narratives</h1>
      <div>
        {narratives.map((narrative) => (
          <Card key={narrative.id} narrative={narrative} />
        ))}
      </div>
    </div>
  );
} 