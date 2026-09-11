import React, { useContext, useState } from "react";
import {EditButton, List, Show, ShowButton} from "@refinedev/antd";
import { Calendar, momentLocalizer, View } from "react-big-calendar";
import moment from "moment";
import "react-big-calendar/lib/css/react-big-calendar.css";
import "@/src/styles/calendar-dark-mode.css";
import { InstrumentSession } from "@/src/type";
import {BaseRecord, useList} from "@refinedev/core";
import {useNavigate, useSearchParams} from "react-router";
import { ColorModeContext } from "@/src/contexts/color-mode";
import { Segmented, Space, Table, Typography } from "antd";

const localizer = momentLocalizer(moment);

const CALENDAR_VIEWS: View[] = ["month", "week", "work_week", "day", "agenda"];
const isCalendarView = (value: string | null): value is View =>
    !!value && (CALENDAR_VIEWS as string[]).includes(value);

export const InstrumentSessionList = () => {
    // The calendar's position (date + zoom level) and the calendar/table toggle
    // live in the URL's query params, not plain component state. This component
    // unmounts when you navigate to edit/show a session, so plain state would
    // reset to "today, month view" on the way back — the bug being fixed here.
    // Query params survive that unmount/remount, and going back in browser
    // history (the default "back" behavior on the edit/show pages) lands on
    // this exact URL again.
    const [searchParams, setSearchParams] = useSearchParams();

    const [view, setView] = useState<"calendar" | "table">(
        searchParams.get("listView") === "table" ? "table" : "calendar"
    );
    const [calendarDate, setCalendarDate] = useState<Date>(() => {
        const raw = searchParams.get("calDate");
        const parsed = raw ? new Date(raw) : null;
        return parsed && !isNaN(parsed.getTime()) ? parsed : new Date();
    });
    const [calendarView, setCalendarView] = useState<View>(() => {
        const raw = searchParams.get("calView");
        return isCalendarView(raw) ? raw : "month";
    });

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

    // `replace: true` so panning the calendar (or flipping table/calendar)
    // updates the current history entry in place instead of piling up one
    // per click — otherwise the back button would need several presses just
    // to leave the list page.
    const updateParams = (patch: Record<string, string>) => {
        setSearchParams(
            (prev) => {
                const next = new URLSearchParams(prev);
                Object.entries(patch).forEach(([key, value]) => next.set(key, value));
                return next;
            },
            { replace: true }
        );
    };

    const handleViewToggle = (value: "calendar" | "table") => {
        setView(value);
        updateParams({ listView: value });
    };

    const handleCalendarNavigate = (newDate: Date) => {
        setCalendarDate(newDate);
        updateParams({ calDate: newDate.toISOString() });
    };

    const handleCalendarViewChange = (newView: View) => {
        setCalendarView(newView);
        updateParams({ calView: newView });
    };

    return (
        <List
            headerButtons={({ defaultButtons }) => (
                <>
                    <Segmented
                        value={view}
                        onChange={(value) => handleViewToggle(value as "calendar" | "table")}
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
                        date={calendarDate}
                        view={calendarView}
                        onNavigate={handleCalendarNavigate}
                        onView={handleCalendarViewChange}
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
