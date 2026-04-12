'use client'

import { useState, useEffect, useCallback } from 'react'

export interface LocationData {
  country: string
  city: string
  countryCode: string
  latitude: number
  longitude: number
}

export type LocationPermission = 'prompt' | 'granted' | 'denied' | 'unsupported'

interface GeolocationState {
  location: LocationData | null
  permission: LocationPermission
  isLoading: boolean
  error: string | null
}

export function useGeolocation() {
  const [state, setState] = useState<GeolocationState>({
    location: null,
    permission: 'prompt',
    isLoading: false,
    error: null
  })

  const reverseGeocode = async (lat: number, lon: number): Promise<LocationData | null> => {
    try {
      // Using Nominatim (OpenStreetMap) for reverse geocoding
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=10&addressdetails=1`,
        {
          headers: {
            'User-Agent': 'TED-Search-Assistant'
          }
        }
      )
      
      if (!response.ok) throw new Error('Geocoding failed')
      
      const data = await response.json()
      const address = data.address || {}
      
      return {
        country: address.country || 'Unknown',
        city: address.city || address.town || address.village || 'Unknown',
        countryCode: address.country_code?.toUpperCase() || 'XX',
        latitude: lat,
        longitude: lon
      }
    } catch (error) {
      console.error('Reverse geocoding error:', error)
      return null
    }
  }

  const requestLocation = useCallback(async () => {
    if (!navigator.geolocation) {
      setState(prev => ({
        ...prev,
        permission: 'unsupported',
        error: 'Geolocation is not supported by your browser'
      }))
      return
    }

    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: false,
          timeout: 10000,
          maximumAge: 300000 // Cache for 5 minutes
        })
      })

      const { latitude, longitude } = position.coords
      const locationData = await reverseGeocode(latitude, longitude)

      if (locationData) {
        setState({
          location: locationData,
          permission: 'granted',
          isLoading: false,
          error: null
        })
      } else {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: 'Could not determine your location'
        }))
      }
    } catch (error: any) {
      console.error('Geolocation error:', error)
      
      let errorMessage = 'Failed to get location'
      let permission: LocationPermission = 'denied'
      
      if (error.code === 1) {
        errorMessage = 'Location permission denied'
        permission = 'denied'
      } else if (error.code === 2) {
        errorMessage = 'Location unavailable'
      } else if (error.code === 3) {
        errorMessage = 'Location request timeout'
      }

      setState({
        location: null,
        permission,
        isLoading: false,
        error: errorMessage
      })
    }
  }, [])

  const resetPermission = useCallback(() => {
    setState({
      location: null,
      permission: 'prompt',
      isLoading: false,
      error: null
    })
  }, [])

  return {
    ...state,
    requestLocation,
    resetPermission
  }
}
