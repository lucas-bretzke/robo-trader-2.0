/**
 * Filter functions for different types of assets
 */

/**
 * Checks if an asset is a binary option
 * Binary options usually have specific identifiers in their name or properties
 * @param {Object} asset - The asset object to check
 * @returns {boolean} - True if the asset is a binary option
 */
export const isBinaryOption = asset => {
  // Common identifiers for binary options assets
  // Adjust these criteria based on your actual asset structure and naming conventions

  if (!asset) return false

  // Check for common binary option identifiers in name or type property
  const name = (asset.name || '').toLowerCase()
  const type = (asset.type || '').toLowerCase()
  const symbol = (asset.symbol || '').toLowerCase()

  // Binary options typically have these identifiers
  return (
    type === 'binary' ||
    type === 'binary_option' ||
    name.includes('binary') ||
    symbol.includes('bo_') ||
    (asset.expiry_type &&
      ['turbo', 'binary', 'digital'].some(term =>
        (asset.expiry_type || '').toLowerCase().includes(term)
      ))
  )
}

/**
 * Filters an array of assets to return only binary options
 * @param {Array} assets - Array of asset objects
 * @returns {Array} - Filtered array containing only binary options
 */
export const filterBinaryOptions = assets => {
  if (!Array.isArray(assets)) return []
  return assets.filter(isBinaryOption)
}
