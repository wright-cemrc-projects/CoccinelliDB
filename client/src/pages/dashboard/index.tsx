import { useEffect, useRef, useState } from "react";
import { Card, Empty, Spin, Tag, Typography } from "antd";
import { useNavigation } from "@refinedev/core";
import axios from "axios";

const { Title, Text } = Typography;

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8080/api";

interface DashboardCollection {
    id: number;
    collection_type: string | null;
    start_date: string | null;
    end_date: string | null;
    session_id: number;
    instrument_id: number | null;
    tilt_series_count: number;
    thumbnails: string[];
}

function formatDate(iso: string | null): string {
    if (!iso) return "—";
    return new Date(iso).toLocaleString();
}

export const DashboardPage = () => {
    const [collections, setCollections] = useState<DashboardCollection[]>([]);
    const [loading, setLoading] = useState(true);
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const fetchCollections = async () => {
        try {
            const response = await axios.get(`${API_URL}/dashboard/collections`, {
                withCredentials: true,
            });
            setCollections(response.data.collections ?? []);
        } catch (err) {
            // Leave existing collections visible on transient errors
            console.error("Failed to fetch dashboard collections", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchCollections();
        intervalRef.current = setInterval(fetchCollections, 15000);
        return () => {
            if (intervalRef.current !== null) {
                clearInterval(intervalRef.current);
            }
        };
    }, []);

    if (loading) {
        return (
            <div style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
                <Spin size="large" tip="Loading collections..." />
            </div>
        );
    }

    return (
        <div style={{ padding: "24px" }}>
            <Title level={3} style={{ marginBottom: 24 }}>
                Active Collections
            </Title>

            {collections.length === 0 ? (
                <Empty description="No active or recent collections found for your sessions." />
            ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                    {collections.map((col) => (
                        <CollectionCard key={col.id} collection={col} />
                    ))}
                </div>
            )}
        </div>
    );
};

interface CollectionCardProps {
    collection: DashboardCollection;
}

function CollectionCard({ collection }: CollectionCardProps) {
    const { show } = useNavigation();
    const isOngoing = collection.end_date === null;

    const title = (
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span>
                Collection #{collection.id}
                {collection.collection_type ? ` — ${collection.collection_type}` : ""}
            </span>
            {isOngoing ? (
                <Tag color="green">Ongoing</Tag>
            ) : (
                <Tag color="default">Completed</Tag>
            )}
            <Text type="secondary" style={{ fontSize: 13, fontWeight: "normal" }}>
                Session #{collection.session_id} &nbsp;|&nbsp; Started {formatDate(collection.start_date)}
            </Text>
        </div>
    );

    const extra = (
        <Text type="secondary" style={{ fontSize: 13 }}>
            {collection.tilt_series_count} tilt series
        </Text>
    );

    return (
        <Card
            title={title}
            extra={extra}
            size="small"
            hoverable
            onClick={() => show("collection", collection.id)}
        >
            {collection.thumbnails.length === 0 ? (
                <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description="No tilt-series thumbnails found in data location."
                    style={{ margin: "12px 0" }}
                />
            ) : (
                <div
                    style={{
                        display: "flex",
                        flexDirection: "row",
                        gap: 8,
                        overflowX: "auto",
                        paddingBottom: 8,
                    }}
                >
                    {collection.thumbnails.map((path) => (
                        <img
                            key={path}
                            src={`${API_URL}/dashboard/images/${collection.id}/${path}`}
                            alt={path}
                            style={{
                                height: 160,
                                width: "auto",
                                objectFit: "cover",
                                borderRadius: 4,
                                flexShrink: 0,
                            }}
                        />
                    ))}
                </div>
            )}
        </Card>
    );
}
