import { useEffect, useState } from "react";
import { DeleteButton, Show, TextField } from "@refinedev/antd";
import { useGetIdentity, useNavigation, useShow } from "@refinedev/core";
import { Card, Col, Empty, Row, Tag, Typography } from "antd";
import axios from "axios";
import { useNavigate } from "react-router";
import { Collection, TiltSeries } from "@/src/type";

const { Title, Link, Text } = Typography;

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8080/api";

export const CollectionShow = () => {
    const { query } = useShow<Collection>({});
    const { data, isLoading } = query;
    const { show, list } = useNavigation();
    const navigate = useNavigate();
    // Deleting a collection is restricted to Admins on the backend; the button
    // is hidden for everyone else rather than shown-then-rejected. Every other
    // role sharing "collection" access (e.g. Editor) still gets full read/edit.
    const { data: identity } = useGetIdentity<{ roles?: string[] }>();
    const isAdmin = (identity?.roles ?? []).some((role) => role.toLowerCase() === "admin");

    const record = data?.data;

    const [tiltSeries, setTiltSeries] = useState<TiltSeries[]>([]);
    const [tiltSeriesLoading, setTiltSeriesLoading] = useState(true);

    useEffect(() => {
        if (!record?.id) return;
        setTiltSeriesLoading(true);
        axios
            .get(`${API_URL}/collection/${record.id}/tiltseries`, { withCredentials: true })
            .then((response) => setTiltSeries(response.data.tilt_series ?? []))
            .catch((err) => console.error("Failed to fetch tilt series", err))
            .finally(() => setTiltSeriesLoading(false));
    }, [record?.id]);

    return (
        <Show
            isLoading={isLoading}
            headerButtons={({ defaultButtons }) => (
                <>
                    {defaultButtons}
                    {isAdmin && (
                        <DeleteButton
                            recordItemId={record?.id}
                            onSuccess={() => list("collection")}
                        />
                    )}
                </>
            )}
        >
            <Title level={5}>{"ID"}</Title>
            <TextField value={record?.id} />

            <Title level={5}>{"Type"}</Title>
            <TextField value={record?.collection_type ?? "—"} />

            <Title level={5}>{"Data Location"}</Title>
            <TextField value={record?.data_location ?? "—"} />

            <Title level={5}>{"Thumbnail Location"}</Title>
            <TextField value={record?.thumbnail_location ?? "(same as Data Location)"} />

            <Title level={5}>{"Start"}</Title>
            <TextField value={record?.start_date ? new Date(record.start_date).toLocaleString() : "—"} />

            <Title level={5}>{"End"}</Title>
            <TextField value={record?.end_date ? new Date(record.end_date).toLocaleString() : "—"} />

            <Title level={5}>{"Image Count"}</Title>
            <TextField value={record?.total_image_count ?? "—"} />

            <Title level={5}>{"Instrument Session"}</Title>
            {record?.instrument_session_id ? (
                <Link onClick={() => show("instrumentsession", record.instrument_session_id)}>
                    Session #{record.instrument_session_id}
                </Link>
            ) : (
                "—"
            )}

            <Title level={5} style={{ marginTop: 24 }}>{"Tilt Series"}</Title>
            {!tiltSeriesLoading && tiltSeries.length === 0 ? (
                <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description="No tilt-series folders found in data location."
                />
            ) : (
                <Row gutter={[16, 16]}>
                    {tiltSeries.map((ts) => {
                        const thumbnail = ts.tomogram_image ?? ts.align_image;
                        return (
                            <Col key={ts.name} xs={24} sm={12} md={8} lg={6}>
                                <Card
                                    hoverable
                                    size="small"
                                    cover={
                                        thumbnail ? (
                                            <img
                                                src={`${API_URL}/collection/${record?.id}/images/${thumbnail}`}
                                                alt={ts.name}
                                                style={{ height: 160, objectFit: "cover" }}
                                            />
                                        ) : undefined
                                    }
                                    onClick={() => navigate(`/collection/${record?.id}/tiltseries/${ts.name}`)}
                                >
                                    <Card.Meta
                                        title={ts.name}
                                        description={
                                            <>
                                                <Tag>{ts.tilt_count} tilts</Tag>
                                                {ts.min_angle !== null && ts.max_angle !== null ? (
                                                    <Text type="secondary" style={{ fontSize: 12 }}>
                                                        {ts.min_angle}° to {ts.max_angle}°
                                                    </Text>
                                                ) : null}
                                            </>
                                        }
                                    />
                                </Card>
                            </Col>
                        );
                    })}
                </Row>
            )}
        </Show>
    );
};
