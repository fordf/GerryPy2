import React from 'react';

class JumpButton extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      jumpSize: 10
    };
  }

  render() {
    return (
      <div className="jump-div">
        <button className="jump-button"
          onClick={() => this.props.onClick(this.state.jumpSize)}>
          {this.props.direction}
        </button>
        <input
          className='jump-input'
          type="number"
          defaultValue={this.state.jumpSize}
          min="1"
          onChange={(event) => {
            this.setState({jumpSize: parseInt(event.target.value, 10)})
          }}/>
      </div>
    );
  }
}

export default JumpButton;