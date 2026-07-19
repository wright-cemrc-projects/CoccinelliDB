import {Edit, useForm, useSelect} from "@refinedev/antd";
import {useNavigation} from "@refinedev/core";
import {Form, Input, InputNumber, DatePicker, Select, Table, Switch, Button, Typography} from "antd";
import {Collection, Facility, Instrument, Person, Project} from "@/src/type";
import {useEffect, useState} from "react";
import {DeleteOutlined, PlusOutlined} from "@ant-design/icons";

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

    const { show } = useNavigation();

    const { formProps, saveButtonProps, queryResult } = useForm({
        mutationMode: "pessimistic",
        metaData: {
            onSubmit: (values: any) => {
                return { ...values, persons };
            },
        },
    });

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
                    <Table
                        dataSource={queryResult?.data?.data?.collections ?? []}
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
        </Edit>
    );
};
