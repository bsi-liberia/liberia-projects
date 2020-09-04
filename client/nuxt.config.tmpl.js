
export default {
  mode: 'universal',
  /*
  ** Headers of the page
  */
  publicRuntimeConfig: {
    title: 'Liberia Project Dashboard',
    baseURL: 'http://127.0.0.1:5000/api'
  },
  head: {
    title: 'Liberia Project Dashboard',
    meta: [
      { charset: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      { hid: 'description', name: 'description', content: process.env.npm_package_description || '' }
    ],
    link: [
      { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }
    ]
  },
  /*
  ** Customize the progress-bar color
  */
  loading: { color: '#fff' },
  /*
  ** Global CSS
  */
  css: [
  ],
  /*
  ** Plugins to load before mounting the App
  */
  plugins: [
    '~/plugins/errors',
    {src: '~/plugins/vue2-leaflet-markercluster.js', mode: 'client'}
  ],
  /*
  ** Nuxt.js dev-modules
  */
  buildModules: [
    '@nuxtjs/fontawesome'
  ],
  /*
  ** Nuxt.js modules
  */
  modules: [
    // Doc: https://bootstrap-vue.js.org
    'bootstrap-vue/nuxt',
    // Doc: https://axios.nuxtjs.org/usage
    '@nuxtjs/axios',
    '@nuxtjs/auth',
    'nuxt-leaflet',
    '@nuxtjs/markdownit',
    'nuxt-vue-select',
    'nuxt-purgecss'
  ],
  fontawesome: {
    icons: {
      solid: ['faCog', 'faTrashAlt', 'faPlus', 'faExclamationCircle',
       'faMagic', 'faClipboardList', 'faSave', 'faLock', 'faLockOpen',
       'faTrash', 'faCheckCircle', 'faTimesCircle', 'faQuestionCircle',
       'faUpload', 'faDownload' , 'faEdit', 'faFilter'],
      regular: ['faCheckCircle', 'faTimesCircle']
    }
  },
  markdownit: {
    preset: 'default',
    linkify: true,
    use: [
    [
      'markdown-it-anchor', { permalink: true, permalinkBefore: true }
    ]
    ]
  },
  /*
  ** Axios module configuration
  ** See https://axios.nuxtjs.org/options
  */
  auth: {
    localStorage: false,
    strategies: {
      local: {
        endpoints: {
          login: { url: '/login/', method: 'post', propertyName: 'access_token' },
          logout: { url: '/logout/', method: 'get'},
          user: { url: '/user/', method: 'get', propertyName: 'user' }
        }
      }
    },
    redirect: {
      logout: '/login',
      home: '/'
    }
  },
  axios: {
    baseURL: 'http://127.0.0.1:5000/api'
  },
  /*
  ** Build configuration
  */
  build: {
    /*
    ** You can extend webpack config here
    */
    extend (config, ctx) {
      config.externals = {
        moment: 'moment'
      }
    }
  }
}
