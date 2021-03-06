import React from 'react';
import PropTypes from 'prop-types';
import { gettext } from '../../utils/constants';
import ReviewListItem from './review-list-item';

const propTypes = {
  isItemFreezed: PropTypes.bool.isRequired,
  itemsList: PropTypes.array.isRequired,
};

class ReviewListView extends React.Component {

  render() {
    let items = this.props.itemsList;
    return (
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th style={{width: '4%'}}>{/*img*/}</th>
              <th style={{width: '26%'}}>{gettext('Name')}</th>
              <th style={{width: '20%'}}>{gettext('Library')}</th>
              <th style={{width: '20%'}}>{gettext('Status')}</th>
              <th style={{width: '20%'}}>{gettext('Last Update')}</th>
              <th style={{width: '10%'}}></th>
            </tr>
          </thead>
          <tbody>
            { items && items.map((item) => {
              return (
                <ReviewListItem 
                  key={item.id} 
                  item={item} 
                  isItemFreezed={this.props.isItemFreezed}
                />
              );
            })}
          </tbody>
        </table>
     </div>
    );
  }
}

ReviewListView.propTypes = propTypes;

export default ReviewListView;
