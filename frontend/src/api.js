// -*- coding: utf-8 -*-
// 统一的后端接口入口：所有请求都走这个 axios 实例
// baseURL 为 /api，开发时由 vite.config.js 里的 proxy 转发到后端 8000 端口
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 5000,
})

export default api
