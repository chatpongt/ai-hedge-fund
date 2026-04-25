import { useCallback, useMemo } from 'react'
import { ReactFlow, Node, Edge, Background, Controls } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Plant, GardenZone, HEALTH_COLORS } from '@/types/garden'

interface Props {
  zones: GardenZone[]
  plants: Plant[]
  selectedPlantId?: string
  onSelectPlant: (id: string) => void
}

export default function GardenMap({ zones, plants, selectedPlantId, onSelectPlant }: Props) {
  const nodes: Node[] = useMemo(() => {
    const zoneNodes: Node[] = zones.map((z, i) => ({
      id: `zone-${z.id}`,
      type: 'default',
      position: { x: i * 420, y: 0 },
      data: { label: z.name },
      style: {
        width: 380, height: 300,
        backgroundColor: '#f0fdf4', border: '2px dashed #86efac',
        borderRadius: 12, fontSize: 14, fontWeight: 600, color: '#16a34a',
        zIndex: -1,
      },
    }))

    const plantNodes: Node[] = plants.map(p => ({
      id: p.id,
      type: 'default',
      position: { x: p.positionX + zones.findIndex(z => z.id === p.zoneId) * 420, y: p.positionY },
      data: { label: p.name.replace(/ #\d+/, '') },
      style: {
        width: 90, height: 40,
        backgroundColor: HEALTH_COLORS[p.healthStatus] + '22',
        border: `2px solid ${HEALTH_COLORS[p.healthStatus]}`,
        borderRadius: 8, fontSize: 11,
        boxShadow: selectedPlantId === p.id ? `0 0 0 3px ${HEALTH_COLORS[p.healthStatus]}` : undefined,
      },
    }))

    return [...zoneNodes, ...plantNodes]
  }, [zones, plants, selectedPlantId])

  const edges: Edge[] = []

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    if (!node.id.startsWith('zone-')) onSelectPlant(node.id)
  }, [onSelectPlant])

  return (
    <div className="card h-full" style={{ minHeight: 340 }}>
      <ReactFlow
        nodes={nodes} edges={edges}
        onNodeClick={onNodeClick}
        fitView
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        className="rounded-lg"
      >
        <Background color="#d1fae5" gap={20} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  )
}
