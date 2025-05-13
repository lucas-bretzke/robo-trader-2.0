import api from './api'
import { BINARY_OPTIONS } from '../config/binaries'

export async function getAvailableAssets() {
  const allAssets = await api.send({
    name: 'get_all_available_assets',
    msg: {}
  })

  // Filter only the assets we're interested in
  const filteredAssets = allAssets.filter(
    asset =>
      BINARY_OPTIONS.includes(asset.name) ||
      BINARY_OPTIONS.includes(asset.display_name) ||
      BINARY_OPTIONS.includes(asset.symbol)
  )

  console.log(`${filteredAssets.length} ativos carregados`)
  return filteredAssets
}
