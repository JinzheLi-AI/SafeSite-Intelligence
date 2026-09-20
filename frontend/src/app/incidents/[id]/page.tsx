import { IncidentDetail } from "@/components/incident-detail";
export default async function IncidentPage({ params }: { params: Promise<{ id: string }> }) {
 const { id } = await params; return <IncidentDetail id={id} />; }
