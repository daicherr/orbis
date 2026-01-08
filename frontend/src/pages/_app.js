import '../styles/globals.css'
import { GameProvider } from '../contexts/GameContext'

export default function App({ Component, pageProps }) {
  return (
    <GameProvider>
      <Component {...pageProps} />
    </GameProvider>
  )
}
