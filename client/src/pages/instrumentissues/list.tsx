import React, { useContext } from "react";
import { List, Show } from "@refinedev/antd";
import { Calendar, momentLocalizer } from "react-big-calendar";
import moment from "moment";
import "react-big-calendar/lib/css/react-big-calendar.css";
import "@/src/styles/calendar-dark-mode.css";
import { InstrumentIssue } from "@/src/type";
import {useList} from "@refinedev/core";
import {useNavigate} from "react-router";
import { ColorModeContext } from "@/src/contexts/color-mode";

const localizer = momentLocalizer(moment);

export const InstrumentIssueList = () => {
    const { data } = useList<InstrumentIssue>({
        resource: "instrumentissues",
    });
    const navigate = useNavigate();
    const { mode } = useContext(ColorModeContext);

    const events = data?.data.map((issue) => ({
        id: issue.id,
        title: issue.issue_title, // Adjust this to display the appropriate event title
        start: new Date(issue.start_date),
        end: new Date(issue.end_date),
    })) || [];

    return (
        <List>
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
                    onSelectEvent={(event) => navigate(`/instrumentissues/edit/${event.id}`)}
                />
            </Show>
        </List>
    );
};