import React, { useRef, useEffect } from 'react';
import * as d3 from 'd3';
import { GitBranch, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

interface GraphNode {
  id: string;
  label: string;
  type: string;
  size: number;
  pagerank: number;
  betweenness: number;
  community: number;
  risk_score?: number;
  crime_type?: string;
}

interface GraphLink {
  source: string;
  target: string;
  relation: string;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  communities: Record<string, number>;
  centrality_scores: Record<string, number>;
  seed_node: string | null;
  community_count: number;
  node_count: number;
  edge_count: number;
  top_central_nodes: any[];
}

interface GraphPanelProps {
  graphData: GraphData | null;
  onAccusedClick: (accusedId: number) => void;
  onFIRClick: (firId: number) => void;
}

export const GraphPanel: React.FC<GraphPanelProps> = ({ graphData, onAccusedClick, onFIRClick }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0 || !svgRef.current) return;

    const width = containerRef.current?.clientWidth || 500;
    const height = 470;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove(); // Clear previous render

    // Setup zoom container
    const gContainer = svg.append('g').attr('class', 'graph-content');

    const zoomBehavior = d3.zoom()
      .scaleExtent([0.1, 8])
      .on('zoom', (event) => {
        gContainer.attr('transform', event.transform);
      });

    svg.call(zoomBehavior as any);

    // Deep copy data for D3 mutation
    const nodes = graphData.nodes.map((d) => ({ ...d }));
    const links = graphData.links.map((d) => ({
      source: d.source,
      target: d.target,
      relation: d.relation,
    }));

    // Setup simulation
    const simulation = d3.forceSimulation(nodes as any)
      .force('link', d3.forceLink(links as any).id((d: any) => d.id).distance(90))
      .force('charge', d3.forceManyBody().strength(-150))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius((d: any) => (d.size || 10) + 4));

    // Render links
    const link = gContainer.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#1e293b') // slate-800
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 1.5);

    // Render nodes
    const node = gContainer.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('class', 'node-group cursor-pointer')
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended) as any
      );

    // Render node circles
    node.append('circle')
      .attr('r', (d: any) => d.size || 10)
      .attr('fill', (d: any) => {
        if (d.type === 'Accused') return '#f43f5e'; // rose-500
        if (d.type === 'FIR') return '#06b6d4'; // cyan-500
        if (d.type === 'Location') return '#f59e0b'; // amber-500
        if (d.type === 'Victim') return '#3b82f6'; // blue-500
        return '#94a3b8';
      })
      .attr('stroke', '#090d16')
      .attr('stroke-width', 1.5)
      .attr('class', (d: any) => 
        d.id === graphData.seed_node 
          ? 'stroke-cyan-400 stroke-[3px] paint-order-stroke filter drop-shadow-[0_0_8px_rgba(6,182,212,0.6)]' 
          : ''
      );

    // Render labels
    node.append('text')
      .text((d: any) => d.label)
      .attr('x', (d: any) => (d.size || 10) + 4)
      .attr('y', 4)
      .attr('fill', '#94a3b8')
      .attr('font-size', '10px')
      .attr('font-family', 'ui-monospace, monospace')
      .attr('pointer-events', 'none')
      .attr('class', 'select-none font-medium');

    // Tooltip titles
    node.append('title')
      .text((d: any) => {
        let label = `Label: ${d.label}\nType: ${d.type}\nPageRank: ${d.pagerank.toFixed(4)}\nCommunity: ${d.community}`;
        if (d.risk_score !== undefined) {
          label += `\nRisk Score: ${d.risk_score}`;
        }
        if (d.crime_type !== undefined) {
          label += `\nCrime Type: ${d.crime_type}`;
        }
        return label;
      });

    // Click handler mapping to numeric database IDs
    node.on('click', (_event, d: any) => {
      const parts = d.id.split('-');
      const type = parts[0];
      const numericId = parseInt(parts[1], 10);
      if (type === 'accused') {
        onAccusedClick(numericId);
      } else if (type === 'fir') {
        onFIRClick(numericId);
      }
    });

    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node
        .attr('transform', (d: any) => `translate(${d.x}, ${d.y})`);
    });

    // Drag helper functions
    function dragstarted(_event: any, d: any) {
      if (!_event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(_event: any, d: any) {
      d.fx = _event.x;
      d.fy = _event.y;
    }

    function dragended(_event: any, d: any) {
      if (!_event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    // Centering shortcut button
    const centerGraph = () => {
      svg.transition().duration(750).call(
        zoomBehavior.transform as any,
        d3.zoomIdentity
      );
    };

    // Expose helpers via windows or standard buttons
    (window as any).centerSiddhiGraph = centerGraph;

  }, [graphData]);

  return (
    <div ref={containerRef} className="glass-panel w-full rounded-lg flex flex-col h-[520px] shadow-2xl relative">
      <div className="p-3 border-b border-slate-800 flex items-center justify-between bg-slate-900/40">
        <div className="flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-rose-500" />
          <h3 className="text-xs font-bold uppercase tracking-widest text-slate-300">
            Criminal Network Graph Lens
          </h3>
        </div>
        
        {/* Visual Legend */}
        <div className="flex items-center gap-3 text-[9px] uppercase tracking-wider font-semibold">
          <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500"></span><span className="text-slate-400">Accused</span></div>
          <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-cyan-500"></span><span className="text-slate-400">FIR</span></div>
          <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500"></span><span className="text-slate-400">Loc</span></div>
          <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500"></span><span className="text-slate-400">Victim</span></div>
        </div>
      </div>

      <div className="flex-1 bg-[#050811] relative overflow-hidden">
        {(!graphData || graphData.nodes.length === 0) ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center p-6 text-slate-500 select-none">
            <GitBranch className="w-12 h-12 text-slate-800 mb-3" />
            <p className="text-xs max-w-xs leading-relaxed uppercase tracking-wider">
              Awaiting query execution. Graph relationships will render automatically on submit.
            </p>
          </div>
        ) : (
          <>
            <svg id="siddhi-d3-graph" ref={svgRef} className="w-full h-full" />
            
            {/* HUD Zoom Controls */}
            <div className="absolute bottom-4 right-4 flex flex-col gap-1.5 bg-slate-950/80 border border-slate-800 p-1.5 rounded-lg shadow-xl backdrop-blur-sm">
              <button
                onClick={() => (window as any).centerSiddhiGraph?.()}
                className="p-1.5 text-slate-400 hover:text-cyan-400 hover:bg-slate-900 rounded transition-colors cursor-pointer"
                title="Recenter"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => d3.select(svgRef.current).transition().duration(300).call(d3.zoom().scaleBy as any, 1.3)}
                className="p-1.5 text-slate-400 hover:text-cyan-400 hover:bg-slate-900 rounded transition-colors cursor-pointer"
                title="Zoom In"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => d3.select(svgRef.current).transition().duration(300).call(d3.zoom().scaleBy as any, 0.7)}
                className="p-1.5 text-slate-400 hover:text-cyan-400 hover:bg-slate-900 rounded transition-colors cursor-pointer"
                title="Zoom Out"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
export default GraphPanel;
