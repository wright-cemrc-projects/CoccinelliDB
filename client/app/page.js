"use client"

import React from 'react'
import { useState, useEffect } from 'react'
import instance from '@/instance';


const Home = () => {
  const [message, setMessage] = useState("");

  useEffect(() => {
    instance.get("home").then(
      response => {
        setMessage(response.data["message"]);
      }
    )
  }, [])
  return (
    <div>
      {message}  
    </div>
  )
}

export default Home
