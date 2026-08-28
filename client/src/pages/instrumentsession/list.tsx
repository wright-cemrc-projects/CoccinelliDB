import React, { useContext, useState } from "react";
import {EditButton, List, Show, ShowButton} from "@refinedev/antd";
import { Calendar, momentLocalizer } from "react-big-calendar";
import moment from "moment";
import "react-big-calendar/lib/css/react-big-calendar.css";
import "@/src/styles/calendar-dark-mode.css";
import { InstrumentSession } from "@/src/type";
import {BaseRecord, useList} from "@refinedev/core";
import {useNavigate} from "react-router";
import { ColorModeContext } from "@/src/contexts/color-mode";
import { Segmented, Space, Table, Typography } from "antd";

const localizer = momentLocalizer(moment);

export const InstrumentSessionList = () => {
    const [view, setView] = useState<"calendar" | "table">("calendar");
    const { data } = useList<InstrumentSession>({
        resource: "instrumentsession",
    });
    const navigate = useNavigate();
    const { mode } = useContext(ColorModeContext);

    const sessions = data?.data ?? [];

    const events = sessions.map((session) => ({
        id: session.id,
        title: `${session.instrument.name}`, // Adjust this to display the appropriate event title
        start: new Date(session.start_date),
        end: new Date(session.end_date),
    }));

    return (
        <List
            headerButtons={({ defaultButtons }) => (
                <>
                    <Segmented
                        value={view}
                        onChange={(value) => setView(value as "calendar" | "table")}
                        options={[
                            { label: "Calendar", value: "calendar" },
                            { label: "Table", value: "table" },
                        ]}
                    />
                    {defaultButtons}
                </>
            )}
        >
            {view === "calendar" ? (
                <Show headerProps={{ extra: null }}>
                    <Calendar
                        localizer={localizer}
                        events={events}
                        startAccessor="start"
                        endAccessor="end"
                        style={{ height: 500 }}
                        className={mode === "dark" ? "rbc-dark-mode" : undefined}
                        defaultView="month"
                        eventPropGetter={(event) => ({
                            style: {
                                backgroundColor: "#1890ff",
                                color: "white",
                                padding: "4px 8px",
                                borderRadius: "4px",
                                fontSize: "12px",
                            },
                        })}
                        onSelectEvent={(event) => navigate(`/instrumentsession/edit/${event.id}`)}
                    />
                </Show>
            ) : (
                <Table
                    dataSource={sessions}
                    rowKey="id"
                    size="small"
                    pagination={{
                        pageSize: 25,
                        showSizeChanger: true,
                        pageSizeOptions: [25, 50, 100, 200],
                    }}
                >
                    <Table.Column dataIndex="id" title="ID" width={70} sorter={(a: InstrumentSession, b: InstrumentSession) => a.id - b.id} />
                    <Table.Column
                        dataIndex={["instrument", "name"]}
                        title="Instrument"
                    />
                    <Table.Column
                        dataIndex="start_date"
                        title="Start"
                        defaultSortOrder="ascend"
                        sorter={(a: InstrumentSession, b: InstrumentSession) =>
                            new Date(a.start_date).getTime() - new Date(b.start_date).getTime()
                        }
                        render={(value: string | null) =>
                            value ? new Date(value).toLocaleString() : "—"
                        }
                    />
                    <Table.Column
                        dataIndex="end_date"
                        title="End"
                        sorter={(a: InstrumentSession, b: InstrumentSession) =>
                            new Date(a.end_date).getTime() - new Date(b.end_date).getTime()
                        }
                        render={(value: string | null) =>
                            value ? new Date(value).toLocaleString() : "—"
                        }
                    />
                    <Table.Column
                        dataIndex="notes"
                        title="Notes"
                        render={(value: string | null) =>
                            value ? (
                                <Typography.Text
                                    ellipsis={{ tooltip: value }}
                                    style={{ maxWidth: 320, display: "inline-block" }}
                                >
                                    {value}
                                </Typography.Text>
                            ) : (
                                "—"
                            )
                        }
                    />
                    <Table.Column
                        title="Actions"
                        dataIndex="actions"
                        render={(_, record: BaseRecord) => (
                            <Space>
                                <ShowButton hideText size="small" recordItemId={record.id} />
                                <EditButton hideText size="small" recordItemId={record.id} />
                            </Space>
                        )}
                    />
                </Table>
            )}
        </List>
    );
};
