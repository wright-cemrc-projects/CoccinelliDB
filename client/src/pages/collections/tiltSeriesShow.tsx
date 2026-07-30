import { useEffect, useState } from "react";
import { useParams } from "react-router";
import { useNavigation } from "@refinedev/core";
import { Descriptions, Empty, Image, Space, Spin, Tag, Typography } from "antd";
import axios from "axios";
import { TiltSeries } from "@/src/type";

const { Title, Link } = Typography;

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8080/api";

export const TiltSeriesShow = () => {
    const { collectionId, name } = useParams<{ collectionId: string; name: string }>();
    const { show } = useNavigation();

    const [tiltSeries, setTiltSeries] = useState<TiltSeries | null>(null);
    const [loading, setLoading] = useState(true);
    const [selectedImage, setSelectedImage] = useState<string | null>(null);

    useEffect(() => {
        if (!collectionId || !name) return;
        setLoading(true);
        axios
            .get(`${API_URL}/collection/${collectionId}/tiltseries/${name}`, { withCredentials: true })
            .then((response) => {
                const data: TiltSeries = response.data;
                setTiltSeries(data);
                setSelectedImage(data.tomogram_image ?? data.align_image ?? null);
            })
            .catch((err) => console.error("Failed to fetch tilt series", err))
            .finally(() => setLoading(false));
    }, [collectionId, name]);

    if (loading) {
        return (
            <div style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
                <Spin size="large" tip="Loading tilt series..." />
            </div>
        );
    }

    if (!tiltSeries) {
        return <Empty description="Tilt series not found." style={{ marginTop: 80 }} />;
    }

    const thumbnails: { label: string; path: string | null }[] = [
        { label: "Tomogram", path: tiltSeries.tomogram_image },
        { label: "Proj XY", path: tiltSeries.tomogram_projxy_image },
        { label: "Proj XZ", path: tiltSeries.tomogram_projxz_image },
        { label: "Align", path: tiltSeries.align_image },
    ].filter((t) => t.path !== null);

    return (
        <div style={{ padding: "24px" }}>
            <Space direction="vertical" size={4} style={{ marginBottom: 24 }}>
                <Title level={3} style={{ margin: 0 }}>
                    {tiltSeries.name}
                </Title>
                <Link onClick={() => show("collection", Number(collectionId))}>
                    ← Back to Collection #{collectionId}
                </Link>
            </Space>

            <div style={{ display: "flex", gap: 32, flexWrap: "wrap" }}>
                <div style={{ flex: "1 1 480px", maxWidth: 640 }}>
                    {selectedImage ? (
                        <Image
                            src={`${API_URL}/collection/${collectionId}/images/${selectedImage}`}
                            alt={tiltSeries.name}
                            style={{ width: "100%", borderRadius: 4 }}
                        />
                    ) : (
                        <Empty description="No images found for this tilt series." />
                    )}

                    {thumbnails.length > 1 && (
                        <div style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
                            {thumbnails.map((t) => (
                                <div
                                    key={t.label}
                                    onClick={() => setSelectedImage(t.path)}
                                    style={{
                                        cursor: "pointer",
                                        border:
                                            selectedImage === t.path
                                                ? "2px solid #1677ff"
                                                : "2px solid transparent",
                                        borderRadius: 4,
                                        overflow: "hidden",
                                    }}
                                >
                                    <img
                                        src={`${API_URL}/collection/${collectionId}/images/${t.path}`}
                                        alt={t.label}
                                        style={{ height: 80, width: 80, objectFit: "cover", display: "block" }}
                                    />
                                    <div style={{ textAlign: "center", fontSize: 12 }}>{t.label}</div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div style={{ flex: "1 1 320px" }}>
                    <Descriptions title="Metadata" column={1} bordered size="small">
                        <Descriptions.Item label="Name">{tiltSeries.name}</Descriptions.Item>
                        <Descriptions.Item label="Tilt Count">{tiltSeries.tilt_count}</Descriptions.Item>
                        <Descriptions.Item label="Angle Range">
                            {tiltSeries.min_angle !== null && tiltSeries.max_angle !== null
                                ? `${tiltSeries.min_angle}° to ${tiltSeries.max_angle}°`
                                : "—"}
                        </Descriptions.Item>
                        <Descriptions.Item label="Tomogram">
                            {tiltSeries.tomogram_image ? (
                                <Tag color="green">Available</Tag>
                            ) : (
                                <Tag color="default">Not available</Tag>
                            )}
                        </Descriptions.Item>
                    </Descriptions>
                </div>
            </div>
        </div>
    );
};
