import config from '../nuxt.config'
import Vue from 'vue'
export const state = () => ({
})

export const mutations = {
}

export const actions = {
}

export const getters = {
  isAuthenticated(state) {
    return state.auth.loggedIn
  },
  loggedInUser(state) {
    return state.auth.user
  }
}
