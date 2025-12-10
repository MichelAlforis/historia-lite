'use client';

import { useState, useEffect } from 'react';
import { ActiveProject, ProjectTemplate, PROJECT_COLORS, ProjectType } from '@/lib/types';
import { getProjects, startProject, cancelProject, accelerateProject } from '@/lib/api';

interface ProjectsPanelProps {
  countryId: string;
  currentYear: number;
  onProjectStarted?: () => void;
}

export default function ProjectsPanel({
  countryId,
  currentYear,
  onProjectStarted,
}: ProjectsPanelProps) {
  const [activeProjects, setActiveProjects] = useState<ActiveProject[]>([]);
  const [availableProjects, setAvailableProjects] = useState<ProjectTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAvailable, setShowAvailable] = useState(false);

  useEffect(() => {
    loadProjects();
  }, [countryId]);

  const loadProjects = async () => {
    try {
      setIsLoading(true);
      const response = await getProjects(countryId);
      setActiveProjects(response.active_projects);
      setAvailableProjects(response.available_projects);
      setError(null);
    } catch (err) {
      setError('Erreur lors du chargement des projets');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartProject = async (projectId: string) => {
    try {
      await startProject(countryId, projectId);
      await loadProjects();
      onProjectStarted?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors du demarrage du projet');
    }
  };

  const handleCancelProject = async (projectId: string) => {
    try {
      await cancelProject(countryId, projectId);
      await loadProjects();
    } catch (err) {
      setError('Erreur lors de l\'annulation');
    }
  };

  const handleAccelerate = async (projectId: string) => {
    try {
      await accelerateProject(countryId, projectId);
      await loadProjects();
    } catch (err) {
      setError('Economie insuffisante pour accelerer');
    }
  };

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="animate-pulse text-gray-400">Chargement des projets...</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">
          Projets ({activeProjects.length})
        </h3>
        <button
          onClick={() => setShowAvailable(!showAvailable)}
          className="text-sm text-blue-400 hover:text-blue-300"
        >
          {showAvailable ? 'Masquer disponibles' : 'Voir disponibles'}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-2 bg-red-900/50 text-red-200 rounded text-sm">
          {error}
        </div>
      )}

      {/* Active Projects */}
      {activeProjects.length > 0 ? (
        <div className="space-y-3">
          {activeProjects.map((project) => (
            <ActiveProjectCard
              key={project.id}
              project={project}
              currentYear={currentYear}
              onCancel={() => handleCancelProject(project.id)}
              onAccelerate={() => handleAccelerate(project.id)}
            />
          ))}
        </div>
      ) : (
        <p className="text-gray-400 text-sm">Aucun projet en cours</p>
      )}

      {/* Available Projects */}
      {showAvailable && (
        <div className="mt-6 pt-4 border-t border-gray-700">
          <h4 className="text-md font-medium text-white mb-3">Projets disponibles</h4>
          <div className="space-y-2">
            {availableProjects.map((template) => (
              <AvailableProjectCard
                key={template.id}
                template={template}
                onStart={() => handleStartProject(template.id)}
                isDisabled={activeProjects.some((p) => p.template_id === template.id)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface ActiveProjectCardProps {
  project: ActiveProject;
  currentYear: number;
  onCancel: () => void;
  onAccelerate: () => void;
}

function ActiveProjectCard({
  project,
  currentYear,
  onCancel,
  onAccelerate,
}: ActiveProjectCardProps) {
  const typeColor = PROJECT_COLORS[project.type as ProjectType] || 'bg-gray-500';
  const yearsRemaining = project.total_years - project.years_active;
  const completionYear = currentYear + yearsRemaining;

  return (
    <div className="bg-gray-700 rounded-lg p-3">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${typeColor}`}></span>
            <h4 className="text-white font-medium">{project.name_fr}</h4>
            {project.accelerated && (
              <span className="px-2 py-0.5 bg-yellow-600 text-yellow-100 text-xs rounded">
                Accelere
              </span>
            )}
            {project.sabotaged && (
              <span className="px-2 py-0.5 bg-red-600 text-red-100 text-xs rounded">
                Sabote
              </span>
            )}
          </div>

          {/* Progress bar */}
          <div className="mt-2">
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>{project.progress}%</span>
              <span>Fin estimee: {completionYear}</span>
            </div>
            <div className="h-2 bg-gray-600 rounded-full overflow-hidden">
              <div
                className={`h-full ${typeColor} transition-all`}
                style={{ width: `${project.progress}%` }}
              />
            </div>
          </div>

          {/* Stats */}
          <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-400">
            <span>Cout/an: {project.economy_cost_per_year}</span>
            <span>Investi: {project.total_invested}</span>
            <span>{project.years_active}/{project.total_years} ans</span>
          </div>

          {/* Completion effects preview */}
          {Object.keys(project.completion_effects).length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {Object.entries(project.completion_effects).map(([stat, value]) => (
                <span
                  key={stat}
                  className="px-1.5 py-0.5 bg-green-900/50 text-green-300 text-xs rounded"
                >
                  {stat}: +{value}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-1 ml-3">
          <button
            onClick={onAccelerate}
            className="px-2 py-1 bg-yellow-600 hover:bg-yellow-700 text-white text-xs rounded transition-colors"
            title="Accelerer (cout double)"
          >
            Accelerer
          </button>
          <button
            onClick={onCancel}
            className="px-2 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition-colors"
          >
            Annuler
          </button>
        </div>
      </div>
    </div>
  );
}

interface AvailableProjectCardProps {
  template: ProjectTemplate;
  onStart: () => void;
  isDisabled: boolean;
}

function AvailableProjectCard({
  template,
  onStart,
  isDisabled,
}: AvailableProjectCardProps) {
  const typeColor = PROJECT_COLORS[template.type as ProjectType] || 'bg-gray-500';

  return (
    <div
      className={`bg-gray-700/50 rounded-lg p-3 ${
        isDisabled ? 'opacity-50' : ''
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${typeColor}`}></span>
            <h5 className="text-white text-sm font-medium">{template.name_fr}</h5>
          </div>
          <p className="text-gray-400 text-xs mt-1">{template.description_fr}</p>

          <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-400">
            <span>{template.total_years} ans</span>
            <span>Cout: {template.economy_cost_per_year}/an</span>
            {template.technology_required > 0 && (
              <span>Tech min: {template.technology_required}</span>
            )}
          </div>

          {/* Effects preview */}
          {Object.keys(template.completion_effects).length > 0 && (
            <div className="mt-1 flex flex-wrap gap-1">
              {Object.entries(template.completion_effects).map(([stat, value]) => (
                <span
                  key={stat}
                  className="px-1 py-0.5 bg-blue-900/50 text-blue-300 text-xs rounded"
                >
                  {stat}: +{value}
                </span>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={onStart}
          disabled={isDisabled}
          className="ml-3 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white text-sm rounded transition-colors"
        >
          {isDisabled ? 'En cours' : 'Demarrer'}
        </button>
      </div>
    </div>
  );
}
