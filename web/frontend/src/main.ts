import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import { setupGlobalErrorHandler } from './utils/errorHandler'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

setupGlobalErrorHandler(app)

app.mount('#app')