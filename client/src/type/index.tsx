export interface Facility {
    id: number;
    name: string;
}

export interface Person {
    primary_contact: boolean;
    id: number;
    first_name: string;
    last_name: string;
    email: string;
    organization: string;
    address1: string;
    address2: string;
    state: string;
    country: string;
    telephone: string;
    net_id: number;
    start_date: Date;
    end_date: Date;
}

export interface Instrument {
    id: number;
    name: string;
    model: string;
}

export interface InstrumentSession {
    id: number;
    start_date: Date;
    end_date: Date;
    instrument: Instrument;
}

export interface InstrumentIssue {
    id: number;
    start_date: Date;
    end_date: Date;
    issue_title: string;
    instrument: Instrument
}

export interface Project {
    id: number;
    project_id: string;
}

export interface Collection {
    id: number;
    data_location: string;
    collection_type: string | null;
    start_date: Date | null;
    end_date: Date | null;
    total_image_count: number | null;
    instrument_session_id: number;
}

export interface RemoteSessionLog {
    id: number;
    start_date: Date;
    end_date: Date | null;
    user_id: number;
    instrument_id: number;
    notes: string | null;
    user?: Pick<Person, "id" | "first_name" | "last_name">;
    instrument?: Pick<Instrument, "id" | "name">;
}
