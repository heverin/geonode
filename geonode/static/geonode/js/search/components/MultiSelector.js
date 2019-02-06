import React from "react";
import PropTypes from "prop-types";
import PubSub from "app/utils/pubsub";
import ellipseString from "app/search/functions/ellipseString";
import toggleProp from "app/search/functions/toggleProp";
import addDisplayNone from "app/search/functions/addDisplayNone";

export default class MultiSelector extends React.Component {
  static propTypes = {
    filter: PropTypes.string,
    model: PropTypes.object,
    hide: PropTypes.bool
  };
  constructor(props) {
    super(props);
    this.model = props.model;
    this.filter = props.filter;
    this.hide = props.hide;
    this.state = {
      selected: false
    };
  }
  getClassName = () => (this.state.selected ? "active" : "");
  toggleClass = () => {
    const newState = toggleProp(this.state, "selected");
    this.setState(newState);
  };

  query = () => {
    const data = {
      selectionType: !this.state.selected ? "select" : "unselect",
      value: this.model.content,
      filter: this.filter
    };
    PubSub.publish("multiSelectClicked", data);
    this.toggleClass();
  };

  getEllipseName = ellipseString(25);

  render = () => (
    <li style={addDisplayNone(this.hide)}>
      <a
        data-value={this.model.value}
        data-filter={this.filter}
        onClick={this.query}
        className={this.getClassName()}
      >
        {this.getEllipseName(this.model.content)}
        <span className="badge pull-right">{this.model.count}</span>
      </a>
    </li>
  );
}
