import React from 'react';
import GoogleMap from 'google-map-react';
import openSocket from 'socket.io-client';

import './App.css';

import JumpButton from './components/JumpButton';

var socket = openSocket('http://localhost:5000');

function subscribeToGeoJson(cb1, cb2) {
  socket.on('tractjson', (geojson) => {
    cb1(null, geojson);
    socket.emit('gotGeoJson');
  });
  socket.on('districtjson', (geojson) => {
    console.log('fullstuff');
    cb2(null, geojson);
  });
  socket.emit('subscribeToGeoJson');
}

class App extends React.PureComponent {

  static defaultProps = {
    center: [39, -105.5],
    zoom: 7,
    coords: {lat: 59.724465, lng: 30.080121}
  };

  constructor(props) {
    super(props);
    this.state = {
      map: null,
      tracts: [],
      tractStep: 0,
      districts: [],
      distStep: 0,
      mode: 'Tracts',
    };
  }

  loadGeoJson(geojson) {
    const geo = JSON.parse(geojson);
    const feature_collection = this.state.map.data.addGeoJson(geo);
    this.setState({
      tracts: this.state.tracts.concat(feature_collection),
      tractStep: this.state.tractStep + feature_collection.length
    })
    this.state.map.data.setStyle(featureStyle);
  }

  saveFullJson(fulljson) {
    this.setState({districts: fulljson});
  }

  initialLoadDistricts() {
    const districts = this.state.map.data.addGeoJson(JSON.parse(this.state.districts))
    this.setState({
      districts: districts,
      distStep: districts.length
    });
    this.state.map.data.setStyle(featureStyle);
  }

  switchMode() {
    if (this.state.mode === 'Tracts') {
      if (typeof this.state.districts === "string") {
        this.clearGeoJson(this.state.tracts);
        this.initialLoadDistricts();
      } else {
        this.clearGeoJson(this.state.tracts);
        this.addGeoJson(this.state.districts);
      }
      this.setState({mode: 'Districts'});
    } else {
      this.clearGeoJson(this.state.districts);
      this.addGeoJson(this.state.tracts);
      this.setState({mode: 'Tracts'});
    }
  }

  jumpBack(steps) {
    const tractmode = this.state.mode === 'Tracts';
    const history = tractmode ? this.state.tracts: this.state.districts;
    const start = tractmode ? this.state.tractStep : this.state.distStep;
    let step;
    for (step = start ; step > 0 && start - step  < steps; step--) {
      this.state.map.data.remove(history[step-1]);
    }
    if (tractmode) {
      this.setState({tractStep: step});
    } else {
      this.setState({distStep: step});
    }
  }

  jumpForward(steps) {
    const tractmode = this.state.mode === 'Tracts';
    const history = tractmode ? this.state.tracts: this.state.districts;
    const start = tractmode ? this.state.tractStep : this.state.distStep;
    let step;
    for (step = start; step < history.length && step - start < steps; step++) {
      this.state.map.data.add(history[step]);
    }
    if (tractmode) {
      this.setState({tractStep: step});
    } else {
      this.setState({distStep: step});
    }
  }

  clearGeoJson(history) {
    for (let feature of history) {
      this.state.map.data.remove(feature);
    }
  }

  addGeoJson(history) {
    for (let feature of history) {
      this.state.map.data.add(feature);
    }
  }

  clearData() {
    this.clearGeoJson(this.state.mode === 'Tracts' ? this.state.tracts : this.state.districts);
    this.setState({tractStep: 0, tracts: [], districts: [], distStep: 0, mode: 'Tracts'});
  }

  render() {
    return (
      <div className="App">
        <header className="App-header">
          <span className="App-title">Gerry<span className='Py'>Py</span></span>
          <button
            className='Generate-button'
            onClick={() => {
              this.clearData();
              subscribeToGeoJson(
                (err, geojson) => this.loadGeoJson(geojson),
                (err, geojson) => {
                  this.state.map.data.setStyle(featureStyle);
                  this.saveFullJson(geojson);
                }
              );
            }}>
            Generate
          </button>
          <button
            style={{display: this.state.districts.length ? 'block' : 'none'}}
            className='Clear-button'
            onClick={() => this.clearData()}>
            Clear
          </button>
          <button
            style={{display: this.state.districts.length ? 'block' : 'none'}}
            className='Full-button'
            onClick={() => this.switchMode()}>
            {this.state.mode}
          </button>
          <div style={{display: this.state.districts.length ? 'block' : 'none'}}>
            <JumpButton
              direction='-'
              onClick={jumpSize => this.jumpBack(jumpSize)}/>
            <JumpButton
              direction='+'
              onClick={jumpSize => this.jumpForward(jumpSize)}/>
          </div>
        </header>
        <div className="Map-container">
          <GoogleMap
            bootstrapURLKeys={{key: "AIzaSyB0v-OlbUtrYA8OJbkwWkILPU9jHpDj6So"}}
            yesIWantToUseGoogleMapApiInternals={true}
            onGoogleApiLoaded={({map, maps}) => this.setState({map})}
            center={this.props.center}
            zoom={this.props.zoom}
            geojson={this.state.geojson}>
          </GoogleMap>
        </div>
        <footer></footer>
      </div>
    );
  }
}

function featureStyle(feature) {
  let color = feature.getProperty('color');
  return ({
    fillColor: color,
    strokeColor: color,
    strokeWeight: 1
  });
}

export default App;
