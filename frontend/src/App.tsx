import './App.css'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import RouteOptimizerPage from './pages/RouteOptimizerPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RouteOptimizerPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
