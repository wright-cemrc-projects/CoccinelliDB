"use client";

import type { DataProvider } from "@refinedev/core";
import dataProviderSimpleRest from "@refinedev/simple-rest";

const API_URL = "https://api.fake-rest.refine.dev";

// export const dataProvider = dataProviderSimpleRest(API_URL);

export const dataProvider: DataProvider = {
    getOne: async ({ resource, id, meta }) => {
      const response = await fetch(`${API_URL}/${resource}/${id}`);
  
      if (response.status < 200 || response.status > 299) throw response;
  
      const data = await response.json();
  
      return { data };
    },
    update: () => {
      throw new Error("Not implemented");
    },
    getList: () => {
      throw new Error("Not implemented");
    },
    create: async ({resource, variables}) => {
        const response = await fetch(`${API_URL}/${resource}`, {
            method: "POST",
            body: JSON.stringify(variables),
            headers: {
              "Content-Type": "application/json",
            },
          });
      
          if (response.status < 200 || response.status > 299) throw response;
      
          const data = await response.json();
      
          return { data };
    },
    deleteOne: () => {
        throw new Error("Not implemented");
    },
    getApiUrl: () => {
        throw new Error("Not implemented");
    }
    /* ... */
  };
