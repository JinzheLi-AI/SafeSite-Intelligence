"use client";
import { createContext, useContext, useState, type ReactNode } from "react";
import { useResource } from "./use-resource";
import type { Project } from "./types";
const ProjectContext = createContext({ projectId: 0, selectProject: (_id: number) => { void _id; }, projects: [] as Project[] });
export function ProjectProvider({ children }: { children: ReactNode }) {
  const resource = useResource<Project[]>("/projects");
  const [selected, selectProject] = useState(0);
  const projects = resource.data ?? [];
  const projectId = projects.some(p => p.id === selected) ? selected : projects[0]?.id ?? 0;
  return <ProjectContext.Provider value={{ projectId, selectProject, projects }}>{children}</ProjectContext.Provider>;
}
export function useProject() { return useContext(ProjectContext); }
