import React from "react";
import {List, Show} from "@refinedev/antd";
import { Calendar, momentLocalizer } from "react-big-calendar";
import moment from "moment";
import "react-big-calendar/lib/css/react-big-calendar.css";
import { InstrumentSession } from "@/src/type";
import {useList} from "@refinedev/core";
import {useNavigate} from "react-router-dom";

const localizer = momentLocalizer(moment);

export const InstrumentSessionList = () => {
    const { data } = useList<InstrumentSession>({
        resource: "instrumentsession",
    });
    const navigate = useNavigate();
    console.log(data);
    const events = data?.data.map((session) => ({
        id: session.id,
        title: `${session.instrument.name}`, // Adjust this to display the appropriate event title
        start: new Date(session.start_date),
        end: new Date(session.end_date),
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
        </List>
    );
};
