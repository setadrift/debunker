import { Link } from "react-router-dom";

type Narrative = {
  id: number;
  summary: string;
  source_count: number;
  last_seen: string;
};

export default function Card({ narrative }: { narrative: Narrative }) {
  return (
    <div className="bg-white shadow-md rounded-lg p-6 mb-4">
      <h2 className="text-xl font-bold mb-2">{narrative.summary}</h2>
      <div className="flex justify-between items-center">
        <span className="text-gray-500">
          Sources: {narrative.source_count}
        </span>
        <span className="text-gray-500">
          Last seen: {new Date(narrative.last_seen).toLocaleDateString()}
        </span>
      </div>
      <Link
        to={`/narratives/${narrative.id}`}
        className="text-blue-500 hover:underline mt-4 inline-block"
      >
        Explore
      </Link>
    </div>
  );
} 