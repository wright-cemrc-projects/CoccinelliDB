import {Edit, useForm, useSelect} from "@refinedev/antd";
import {useNavigation, useOne} from "@refinedev/core";
import {Form, Input, InputNumber, DatePicker, Select, Table, Switch, Button, Space, Tag, Typography} from "antd";
import {Collection, Facility, Instrument, InstrumentSession, Person, Project, SessionGroup} from "@/src/type";
import {useEffect, useState} from "react";
import {DeleteOutlined, LinkOutlined, PlusOutlined, ScissorOutlined} from "@ant-design/icons";
import {SplitSessionModal} from "./splitSessionModal";

import dayjs from 'dayjs';
import utc from "dayjs/plugin/utc";
import timezone from "dayjs/plugin/timezone"

dayjs.extend(utc);
dayjs.extend(timezone);

export const InstrumentSessionEdit = () => {

    const { selectProps: facilitySelectProps } = useSelect({
        resource: "facilities",
        optionLabel: (item: Facility) => `${item?.name}`,
        optionValue: "id",
        onSearch: (value) => [
            {
                field: "name",
                operator: "contains",
                value: value,
            },

        ],
    });

    const { selectProps: instrumentSelectProps } = useSelect({
        resource: "instruments",
        optionLabel: (item: Instrument) => `${item?.name}`,
        optionValue: "id",
        onSearch: (value) => [
            {
                field: "name",
                operator: "contains",
                value: value,
            },

        ],
    });
    const { selectProps: projectSelectProps } = useSelect({
        resource: "projects",
        optionLabel: (item: Project) => `${item?.project_id}`,
        optionValue: "id",
        onSearch: (value) => [
            {
                field: "project_id",
                operator: "contains",
                value: value,
            },

        ],
    });
    const { selectProps: personSelectProps } = useSelect({
        resource: "persons",
        optionLabel: (item: Person) => `${item?.first_name} ${item?.last_name}`,
        optionValue: "id",
        sorters: [
            {
                field: "last_name",
                order: "asc",
            },
        ],
        onSearch: (value) => [
            {
                field: "full_name",
                operator: "contains",
                value: value,
            },
        ],
    });

    const [persons, setPersons] = useState<
        { person_id: number | undefined; onsite: boolean; role: string; hours: number; remote_access_level: string }[]
    >([]);

    const addPerson = () => {
        setPersons([...persons, { person_id: undefined, onsite: false, role: "", hours: 0, remote_access_level: "" }]);
    };

    const removePerson = (index: number) => {
        setPersons(persons.filter((_, i) => i !== index));
    };

    const updatePerson = (index: number, key: string, value: any) => {
        const updatedPersons = [...persons];
        updatedPersons[index] = { ...updatedPersons[index], [key]: value };
        setPersons(updatedPersons);
    };

    const { selectProps: sessionGroupSelectProps } = useSelect({
        resource: "sessiongroups",
        optionLabel: (item: SessionGroup) => item?.name ?? `Group ${item?.id}`,
        optionValue: "id",
        onSearch: (value) => [
            {
                field: "name",
                operator: "contains",
                value: value,
            },
        ],
    });

    const { show, list, edit } = useNavigation();
    const [splitOpen, setSplitOpen] = useState(false);

    const { formProps, saveButtonProps, queryResult } = useForm({
        mutationMode: "pessimistic",
        metaData: {
            onSubmit: (values: any) => {
                return { ...values, persons };
            },
        },
    });

    // The record id arrives as refine's BaseKey (string | number); everything downstream wants a number.
    const rawSessionId = queryResult?.data?.data?.id;
    const sessionId = rawSessionId == null ? undefined : Number(rawSessionId);
    const collections: Collection[] = queryResult?.data?.data?.collections ?? [];
    const datedCollectionCount = collections.filter((c) => c.start_date).length;
    const sessionGroupId: number | null = queryResult?.data?.data?.session_group_id ?? null;

    // The other sessions this one is linked to, so the block stays visible from here.
    const { data: groupData } = useOne<SessionGroup>({
        resource: "sessiongroups",
        id: sessionGroupId ?? undefined,
        queryOptions: { enabled: sessionGroupId != null },
    });
    const linkedSessions: InstrumentSession[] = (groupData?.data?.sessions ?? []).filter(
        (s) => s.id !== sessionId
    );

    const startDate = queryResult?.data?.data?.start_date;
    const endDate = queryResult?.data?.data?.end_date;
    const spansMultipleDays =
        !!startDate && !!endDate &&
        dayjs(endDate).startOf("day").isAfter(dayjs(startDate).startOf("day"));
    const canSplit = spansMultipleDays || datedCollectionCount >= 2;

    useEffect(() => {
        if (queryResult?.data) {
            const persons = queryResult.data.data.persons;
            setPersons(persons || []);
            formProps.form?.setFieldsValue({ persons: persons?.map((p: { person_id: number }) => p.person_id) || [] });
        }
    }, [queryResult?.data]);

    const handleFormSubmit = (values: any) => {
        const payload = { ...values, persons,
            start_date: values.start_date
                ? dayjs(values.start_date).format("YYYY-MM-DDTHH:mm:ss[Z]")
                : null,
            end_date: values.end_date
                ? dayjs(values.end_date).format("YYYY-MM-DDTHH:mm:ss[Z]")
                : null,
        }
        formProps.onFinish?.(payload);
    };

    return (
        <Edit saveButtonProps={saveButtonProps} >
            <Form {...formProps} layout="vertical" onFinish={handleFormSubmit} >
                <Form.Item
                    label={"Start Date"}
                    name={["start_date"]}
                    rules={[
                        {
                            required: true, message: "Start Date is required"
                        },
                    ]}
                    getValueProps={(value) => ({ value: value ? dayjs(value) : "", })}
                >
                    <DatePicker
                        showTime={{ use12Hours: true, format: "HH:mm a" }} // Enables time selection
                        format="YYYY-MM-DD HH:mm:ss" // Adjust this to match your database format
                    />
                </Form.Item>
                <Form.Item
                    label={"End Date"}
                    name={["end_date"]}
                    rules={[
                        {
                            required: true, message: "End Date is required"
                        },
                    ]}
                    getValueProps={(value) => ({ value: value ? dayjs(value) : "", })}
                >
                    <DatePicker
                        showTime={{ use12Hours: true, format: "HH:mm a" }} // Enables time selection
                        format="YYYY-MM-DD HH:mm:ss" // Adjust this to match your database format
                    />
                </Form.Item>
                <Form.Item
                    label={"Facility"}
                    name={["facility_id"]}
                    rules={[
                        {
                            required: true,
                        },
                    ]}
                >
                    <Select
                        {...facilitySelectProps}
                        dropdownStyle={{ padding: "0px" }}
                        style={{ width: "100%" }}

                    />
                </Form.Item>
                <Form.Item
                    label={"Project"}
                    name={["project_id"]}
                    rules={[
                        {
                            required: false,
                        },
                    ]}
                >
                    <Select
                        {...projectSelectProps}
                        dropdownStyle={{ padding: "0px" }}
                        style={{ width: "100%" }}

                    />
                </Form.Item>
                <Form.Item
                    label={"Instrument"}
                    name={["instrument_id"]}
                    rules={[
                        {
                            required: true,
                        },
                    ]}
                >
                    <Select
                        {...instrumentSelectProps}
                        dropdownStyle={{ padding: "0px" }}
                        style={{ width: "100%" }}

                    />
                </Form.Item>
                <Form.Item
                    label={"End of Session Notes"}
                    name={["notes"]}
                >
                    <Input.TextArea
                        rows={6}
                        placeholder="Notes on how the session went..."
                    />
                </Form.Item>
                <Form.Item
                    label={"Session Group"}
                    name={["session_group_id"]}
                    help="Links this session to a block of related sessions — for example the days one long booking was split into, or sessions sharing a collection record."
                >
                    <Select
                        {...sessionGroupSelectProps}
                        allowClear
                        placeholder="Not linked to a group"
                        dropdownStyle={{ padding: "0px" }}
                        style={{ width: "100%" }}
                    />
                </Form.Item>
                {linkedSessions.length > 0 && (
                    <Form.Item label="Linked Sessions">
                        <Space style={{ marginBottom: 10 }}>
                            <Tag icon={<LinkOutlined />}>
                                {groupData?.data?.name ?? `Group ${sessionGroupId}`}
                            </Tag>
                            <Typography.Link onClick={() => show("sessiongroups", sessionGroupId!)}>
                                View the whole block
                            </Typography.Link>
                        </Space>
                        <Table dataSource={linkedSessions} rowKey="id" pagination={false} size="small">
                            <Table.Column dataIndex="id" title="ID" width={70} />
                            <Table.Column
                                dataIndex="start_date"
                                title="Start"
                                render={(value: string | null) =>
                                    value ? dayjs(value).format("YYYY-MM-DD HH:mm") : "—"
                                }
                            />
                            <Table.Column
                                dataIndex="end_date"
                                title="End"
                                render={(value: string | null) =>
                                    value ? dayjs(value).format("YYYY-MM-DD HH:mm") : "—"
                                }
                            />
                            <Table.Column
                                title="Action"
                                render={(_, record: InstrumentSession) => (
                                    <Typography.Link onClick={() => edit("instrumentsession", record.id)}>
                                        Edit
                                    </Typography.Link>
                                )}
                            />
                        </Table>
                    </Form.Item>
                )}
                <Form.Item label="Session Participants" name={["persons"]}>
                    <Table dataSource={persons} rowKey={(_, index) => index!} pagination={false} size="small">
                        <Table.Column
                            title="Person"
                            dataIndex="person_id"
                            render={(value, _, index) => (
                                <Select
                                    {...personSelectProps}
                                    value={value}
                                    placeholder="Select a person"
                                    onChange={(val) => updatePerson(index, "person_id", val)}
                                    style={{ width: "100%" }}
                                />
                            )}
                        />
                        <Table.Column
                            title="Onsite"
                            dataIndex="onsite"
                            render={(value, _, index) => (
                                <Switch checked={value} onChange={(val) => updatePerson(index, "onsite", val)} />
                            )}
                        />
                        <Table.Column
                            title="Role"
                            dataIndex="role"
                            render={(value, _, index) => (
                                <Select
                                    value={value}
                                    onChange={(selectedValue) => updatePerson(index, "role", selectedValue)}
                                    placeholder="Select a role"
                                    style={{ width: "100%" }} 
                                    options={[
                                        { label: "Staff", value: "staff" },
                                        { label: "Trainee", value: "trainee" },
                                        { label: "Independent Operator", value: "operator" },
                                        { label: "Client", value: "client" },
                                        { label: "Observer", value: "observer" },
                                        { label: "Other", value: "other" },
                                    ]}
                                />
                            )}
                        />
                        <Table.Column
                            title="Hours"
                            dataIndex="hours"
                            render={(value, _, index) => (
                                <InputNumber
                                    min={0}
                                    value={value}
                                    onChange={(val) => updatePerson(index, "hours", val ?? 0)}
                                />
                            )}
                        />
                        <Table.Column
                            title="Remote Access Level"
                            dataIndex="remote_access_level"
                            render={(value, _, index) => (
                                <Select
                                    value={value}
                                    onChange={(selectedValue) => updatePerson(index, "remote_access_level", selectedValue)}
                                    placeholder="Select remote access level"
                                    style={{ width: "100%" }} 
                                    options={[
                                        { label: "No access", value: "no access" },
                                        { label: "Remote view", value: "remote view" },
                                        { label: "Remote control", value: "remote control" },
                                    ]}
                                />
                            )}
                        />
                        <Table.Column
                            title="Action"
                            render={(_, __, index) => (
                                <Button danger icon={<DeleteOutlined />} onClick={() => removePerson(index)} />
                            )}
                        />
                    </Table>
                    <Button type="dashed" icon={<PlusOutlined />} onClick={addPerson} style={{ marginTop: 10 }}>
                        Add Person
                    </Button>
                </Form.Item>
                <Form.Item label="Associated Collections">
                    <Button
                        icon={<ScissorOutlined />}
                        onClick={() => setSplitOpen(true)}
                        disabled={!canSplit}
                        style={{ marginBottom: 10 }}
                        title={
                            canSplit
                                ? undefined
                                : "Needs a session spanning more than one day, or at least 2 dated collections"
                        }
                    >
                        Split into Separate Sessions
                    </Button>
                    <Table
                        dataSource={collections}
                        rowKey="id"
                        pagination={false}
                        size="small"
                    >
                        <Table.Column dataIndex="id" title="ID" />
                        <Table.Column
                            dataIndex="collection_type"
                            title="Type"
                            render={(value: string | null) => value ?? "—"}
                        />
                        <Table.Column
                            dataIndex="start_date"
                            title="Start"
                            render={(value: string | null) =>
                                value ? dayjs(value).format("YYYY-MM-DD HH:mm") : "—"
                            }
                        />
                        <Table.Column dataIndex="total_image_count" title="Image Count" />
                        <Table.Column
                            title="Action"
                            render={(_, record: Collection) => (
                                <Typography.Link onClick={() => show("collection", record.id)}>
                                    View
                                </Typography.Link>
                            )}
                        />
                    </Table>
                </Form.Item>
            </Form>
            <SplitSessionModal
                open={splitOpen}
                sessionId={sessionId}
                datedCollectionCount={datedCollectionCount}
                onCancel={() => setSplitOpen(false)}
                onSplit={(_, sessionGroupId) => {
                    setSplitOpen(false);
                    if (sessionGroupId) {
                        show("sessiongroups", sessionGroupId);
                    } else {
                        list("instrumentsession");
                    }
                }}
            />
        </Edit>
    );
};
