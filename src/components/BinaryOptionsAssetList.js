import React, { useState, useEffect } from 'react'
import { filterBinaryOptions } from '../utils/assetFilters'

/**
 * Component to display only binary options assets
 * @param {Object} props - Component properties
 * @param {Array} props.assets - All loaded assets
 * @returns {JSX.Element} - Rendered component
 */
const BinaryOptionsAssetList = ({ assets }) => {
  const [binaryOptions, setBinaryOptions] = useState([])

  useEffect(() => {
    const filteredAssets = filterBinaryOptions(assets)
    setBinaryOptions(filteredAssets)
  }, [assets])

  return (
    <div className='binary-options-container'>
      <h2>Binary Options Assets ({binaryOptions.length})</h2>
      {binaryOptions.length === 0 ? (
        <p>No binary options assets found.</p>
      ) : (
        <div className='binary-options-list'>
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Name</th>
                <th>Type</th>
                <th>Expiry</th>
              </tr>
            </thead>
            <tbody>
              {binaryOptions.map((asset, index) => (
                <tr key={`binary-option-${index}`}>
                  <td>{asset.symbol}</td>
                  <td>{asset.name}</td>
                  <td>{asset.type}</td>
                  <td>{asset.expiry_type || 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default BinaryOptionsAssetList
