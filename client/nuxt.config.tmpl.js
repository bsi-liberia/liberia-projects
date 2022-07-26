
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
      { hid: 'description', name: 'description', content: 'The Liberia Project Dashboard is used to collect, analyze, and report information about external assistance programs and projects in Liberia.' },
      { name: 'twitter:card', content: 'summary_large_image' },
      { name: 'twitter:title', content: 'Liberia Project Dashboard' },
      { name: 'twitter:description', content: 'The Liberia Project Dashboard is used to collect, analyze, and report information about external assistance programs and projects in Liberia.' },
      { name: 'twitter:image', content: 'https://liberiaprojects.org/flag-liberia-large.png' },
      { name: 'twitter:image:alt', content: 'Contributions to the Covid-19 emergency.' }
    ],
    link: [
      { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }
    ]
  },
  /*
  ** Customize the progress-bar color
  */
  loading: { color: '#fff', height: '5px' },
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
    {src: '~/plugins/vue2-leaflet-markercluster.js', mode: 'client'},
    {src: '~plugins/vuedraggable.js'}
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
    'nuxt-vue-select'
  ],
  fontawesome: {
    icons: {
      solid: ['faCog', 'faTrashAlt', 'faPlus', 'faExclamationCircle',
       'faMagic', 'faClipboardList', 'faSave', 'faLock', 'faLockOpen',
       'faTrash', 'faCheckCircle', 'faTimesCircle', 'faQuestionCircle',
       'faUpload', 'faDownload' , 'faEdit', 'faFilter', 'faLink', 'faSearch'],
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
